"""Tests for common ERA5 Single Levels solar transformations."""

import numpy as np
import pandas as pd
import pytest


xr = pytest.importorskip("xarray")
pytest.importorskip("pvlib")

from h2integrate.converters.solar.solar_pysam import PYSAMSolarPlantPerformanceModel
from h2integrate.resource.era5_solar import (
    HOURLY_ACCUMULATION_SECONDS,
    STANDARD_GRAVITY_M_PER_S2,
    transform_era5_solar_dataset,
)


def _solar_point_dataset() -> object:
    """Create a small ERA5 point dataset spanning daytime and nighttime."""

    valid_time = pd.date_range("2023-03-20 01:00:00", periods=24, freq="h")
    ssrd = np.zeros(24)
    fdir = np.zeros(24)
    ssrd[0] = 360_000.0
    fdir[0] = 180_000.0
    ssrd[12] = 3_600_000.0
    fdir[12] = 1_800_000.0
    dataset = xr.Dataset(
        data_vars={
            "ssrd": ("valid_time", ssrd, {"units": "J m**-2"}),
            "fdir": ("valid_time", fdir, {"units": "J m**-2"}),
            "t2m": ("valid_time", np.full(24, 298.15), {"units": "K"}),
            "d2m": ("valid_time", np.full(24, 288.15), {"units": "K"}),
            "sp": ("valid_time", np.full(24, 100_000.0), {"units": "Pa"}),
            "z": (
                "valid_time",
                np.full(24, 1_000.0 * STANDARD_GRAVITY_M_PER_S2),
                {"units": "m**2 s**-2"},
            ),
            "u10": ("valid_time", np.full(24, 3.0), {"units": "m s**-1"}),
            "v10": ("valid_time", np.full(24, 4.0), {"units": "m s**-1"}),
        },
        coords={
            "valid_time": valid_time,
            "latitude": 0.0,
            "longitude": 0.0,
        },
        attrs={
            "dataset": "ERA5 Single Levels",
            "resource_year": 2023,
            "requested_latitude": 0.01,
            "requested_longitude": 0.01,
            "selected_latitude": 0.0,
            "selected_longitude": 0.0,
            "grid_distance_km": 1.57,
            "spatial_method": "nearest",
            "nearest_distance_warning_km": 15.0,
            "data_timezone": "UTC",
            "time_step_seconds": 3600,
            "categories": ("solar", "wind", "auxiliary"),
            "source_files": (
                "solar_2023_03.nc",
                "wind_2023_03.nc",
                "auxiliary_2023_03.nc",
            ),
            "expver_values": ("0001",),
            "number": 0,
        },
    )
    return dataset


@pytest.mark.unit
def test_transform_era5_solar_dataset_applies_radiation_and_unit_conversions():
    resource_data = transform_era5_solar_dataset(_solar_point_dataset())

    assert resource_data["ghi"][12] == pytest.approx(1_000.0)
    assert resource_data["dhi"][12] == pytest.approx(500.0)
    expected_dni = 500.0 / np.cos(np.radians(resource_data["solar_zenith_angle"][12]))
    assert resource_data["dni"][12] == pytest.approx(expected_dni)
    assert resource_data["dni"][0] == 0.0
    assert resource_data["dni_zeroed_by_zenith_count"] == 1

    np.testing.assert_allclose(resource_data["temperature"], 25.0)
    np.testing.assert_allclose(resource_data["dew_point"], 15.0)
    np.testing.assert_allclose(resource_data["pressure"], 1_000.0)
    np.testing.assert_allclose(resource_data["wind_speed"], 5.0)
    assert resource_data["elevation"] == pytest.approx(1_000.0)
    assert resource_data["era5_elevation"] == pytest.approx(1_000.0)
    assert resource_data["data_tz"] == 0.0
    assert resource_data["dt"] == HOURLY_ACCUMULATION_SECONDS
    assert resource_data["solar_geometry_time_offset_seconds"] == -1800
    assert resource_data["start_time"] == "2023/03/20 01:00:00 (+0000)"
    assert resource_data["end_time"] == "2023/03/21 00:00:00 (+0000)"
    assert resource_data["source_units"]["ssrd"] == "J m**-2"


@pytest.mark.unit
def test_fdir_above_ssrd_is_limited_and_reported_without_modifying_source():
    dataset = _solar_point_dataset()
    original_fdir = dataset["fdir"].values.copy()
    dataset["fdir"][12] = 4_500_000.0

    with pytest.warns(UserWarning, match="fdir exceeds ssrd in 1 timestep"):
        resource_data = transform_era5_solar_dataset(dataset)

    assert resource_data["fdir_exceeds_ssrd_count"] == 1
    assert resource_data["dhi"][12] == 0.0
    assert resource_data["ghi"][12] == pytest.approx(1_000.0)
    assert dataset["fdir"].values[0] == original_fdir[0]
    assert dataset["fdir"].values[12] == 4_500_000.0


@pytest.mark.unit
def test_configured_site_elevation_takes_precedence():
    resource_data = transform_era5_solar_dataset(
        _solar_point_dataset(),
        site_elevation_m=1_250.0,
    )

    assert resource_data["elevation"] == pytest.approx(1_250.0)
    assert resource_data["era5_elevation"] == pytest.approx(1_000.0)
    assert resource_data["elevation_source"] == "configured_site"


@pytest.mark.unit
def test_transformed_data_matches_pysam_solar_resource_field_names():
    resource_data = transform_era5_solar_dataset(_solar_point_dataset())

    pysam_data = PYSAMSolarPlantPerformanceModel.format_resource_data(None, resource_data)

    expected_fields = {
        "elev",
        "lat",
        "lon",
        "tz",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "dn",
        "df",
        "gh",
        "wspd",
        "tdry",
        "wdir",
        "pres",
        "tdew",
    }
    assert set(pysam_data) == expected_fields
    assert len(pysam_data["dn"]) == 24
    assert np.isfinite(pysam_data["dn"]).all()


@pytest.mark.unit
def test_transform_rejects_negative_radiation_accumulation():
    dataset = _solar_point_dataset()
    dataset["ssrd"][0] = -1.0

    with pytest.raises(ValueError, match="accumulations must be nonnegative"):
        transform_era5_solar_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_dew_point_above_temperature():
    dataset = _solar_point_dataset()
    dataset["d2m"][0] = dataset["t2m"][0] + 0.2

    with pytest.raises(ValueError, match="d2m cannot exceed t2m"):
        transform_era5_solar_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_invalid_zenith_threshold():
    with pytest.raises(ValueError, match="between 0 and 90"):
        transform_era5_solar_dataset(
            _solar_point_dataset(),
            maximum_zenith_angle_deg=90.0,
        )


@pytest.mark.unit
def test_transform_rejects_missing_required_variable():
    dataset = _solar_point_dataset().drop_vars("fdir")

    with pytest.raises(ValueError, match="missing variables: fdir"):
        transform_era5_solar_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_incompatible_units():
    dataset = _solar_point_dataset()
    dataset["ssrd"].attrs["units"] = "W m**-2"

    with pytest.raises(ValueError, match=r"ssrd has units 'W m\*\*-2'"):
        transform_era5_solar_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_non_utc_data():
    dataset = _solar_point_dataset()
    dataset.attrs["data_timezone"] = "America/Santiago"

    with pytest.raises(ValueError, match="data_timezone='UTC'"):
        transform_era5_solar_dataset(dataset)
