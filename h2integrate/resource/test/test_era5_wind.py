"""Tests for common ERA5 Single Levels wind transformations."""

import numpy as np
import pandas as pd
import pytest


xr = pytest.importorskip("xarray")

from h2integrate.resource.era5_wind import (
    STANDARD_ATMOSPHERE_PA,
    STANDARD_GRAVITY_M_PER_S2,
    transform_era5_wind_dataset,
    wind_components_to_speed_and_direction,
)


def _wind_point_dataset() -> object:
    """Create a small validated ERA5 point dataset with analytical values."""

    valid_time = pd.date_range("2023-01-01", periods=4, freq="h")
    dataset = xr.Dataset(
        data_vars={
            "u10": ("valid_time", [0.0, -1.0, 0.0, 1.0], {"units": "m s**-1"}),
            "v10": ("valid_time", [-1.0, 0.0, 1.0, 0.0], {"units": "m s**-1"}),
            "u100": ("valid_time", [3.0, -3.0, 0.0, 0.0], {"units": "m s**-1"}),
            "v100": ("valid_time", [4.0, 4.0, -5.0, 0.0], {"units": "m s**-1"}),
            "t2m": ("valid_time", [273.15, 274.15, 275.15, 276.15], {"units": "K"}),
            "sp": (
                "valid_time",
                np.full(4, STANDARD_ATMOSPHERE_PA),
                {"units": "Pa"},
            ),
            "z": (
                "valid_time",
                np.full(4, 1_000.0 * STANDARD_GRAVITY_M_PER_S2),
                {"units": "m**2 s**-2"},
            ),
        },
        coords={
            "valid_time": valid_time,
            "latitude": -23.5,
            "longitude": -68.25,
        },
        attrs={
            "dataset": "ERA5 Single Levels",
            "resource_year": 2023,
            "requested_latitude": -23.45,
            "requested_longitude": -68.30,
            "selected_latitude": -23.5,
            "selected_longitude": -68.25,
            "grid_distance_km": 7.3,
            "spatial_method": "nearest",
            "nearest_distance_warning_km": 15.0,
            "data_timezone": "UTC",
            "time_step_seconds": 3600,
            "categories": ("wind", "auxiliary"),
            "source_files": ("wind_2023_01.nc", "auxiliary_2023_01.nc"),
            "expver_values": ("0001",),
            "number": 0,
        },
    )
    return dataset


@pytest.mark.unit
def test_wind_components_use_meteorological_direction_convention():
    speed, direction = wind_components_to_speed_and_direction(
        [0.0, -1.0, 0.0, 1.0],
        [-1.0, 0.0, 1.0, 0.0],
    )

    np.testing.assert_allclose(speed, 1.0)
    np.testing.assert_allclose(direction, [0.0, 90.0, 180.0, 270.0])


@pytest.mark.unit
def test_wind_components_reject_different_shapes():
    with pytest.raises(ValueError, match="identical shapes"):
        wind_components_to_speed_and_direction([1.0, 2.0], [1.0])


@pytest.mark.unit
def test_transform_era5_wind_dataset_matches_h2integrate_contract():
    resource_data = transform_era5_wind_dataset(_wind_point_dataset())

    np.testing.assert_allclose(resource_data["wind_speed_10m"], 1.0)
    np.testing.assert_allclose(
        resource_data["wind_direction_10m"],
        [0.0, 90.0, 180.0, 270.0],
    )
    np.testing.assert_allclose(resource_data["wind_speed_100m"], [5.0, 5.0, 5.0, 0.0])
    assert resource_data["wind_direction_100m"][-1] == pytest.approx(270.0)
    np.testing.assert_allclose(resource_data["temperature_2m"], [0.0, 1.0, 2.0, 3.0])
    np.testing.assert_allclose(resource_data["pressure_0m"], 1.0)

    assert resource_data["site_lat"] == pytest.approx(-23.5)
    assert resource_data["site_lon"] == pytest.approx(-68.25)
    assert resource_data["elevation"] == pytest.approx(1_000.0)
    assert resource_data["era5_elevation"] == pytest.approx(1_000.0)
    assert resource_data["elevation_source"] == "ERA5_geopotential"
    assert resource_data["data_tz"] == 0.0
    assert resource_data["dt"] == 3600
    assert resource_data["start_time"] == "2023/01/01 00:00:00 (+0000)"
    assert resource_data["end_time"] == "2023/01/01 03:00:00 (+0000)"
    np.testing.assert_array_equal(resource_data["hour"], [0.0, 1.0, 2.0, 3.0])
    assert resource_data["source_files"] == (
        "wind_2023_01.nc",
        "auxiliary_2023_01.nc",
    )
    assert resource_data["source_units"]["sp"] == "Pa"
    assert resource_data["spatial_method"] == "nearest"


@pytest.mark.unit
def test_configured_site_elevation_takes_precedence_and_preserves_era5_value():
    resource_data = transform_era5_wind_dataset(
        _wind_point_dataset(),
        site_elevation_m=1_250.0,
    )

    assert resource_data["elevation"] == pytest.approx(1_250.0)
    assert resource_data["era5_elevation"] == pytest.approx(1_000.0)
    assert resource_data["elevation_source"] == "configured_site"


@pytest.mark.unit
def test_transform_rejects_missing_required_variable():
    dataset = _wind_point_dataset().drop_vars("sp")

    with pytest.raises(ValueError, match="missing variables: sp"):
        transform_era5_wind_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_incompatible_units():
    dataset = _wind_point_dataset()
    dataset["sp"].attrs["units"] = "hPa"

    with pytest.raises(ValueError, match="sp has units 'hPa'"):
        transform_era5_wind_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_non_utc_data():
    dataset = _wind_point_dataset()
    dataset.attrs["data_timezone"] = "America/Santiago"

    with pytest.raises(ValueError, match="data_timezone='UTC'"):
        transform_era5_wind_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_nonpositive_pressure():
    dataset = _wind_point_dataset()
    dataset["sp"][0] = 0.0

    with pytest.raises(ValueError, match="strictly positive pressure"):
        transform_era5_wind_dataset(dataset)


@pytest.mark.unit
def test_transform_rejects_time_varying_surface_geopotential():
    dataset = _wind_point_dataset()
    dataset["z"][1] += 1.0

    with pytest.raises(ValueError, match="must remain constant"):
        transform_era5_wind_dataset(dataset)
