"""Tests for the common ERA5 Single Levels reader."""

import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


xr = pytest.importorskip("xarray")
pytest.importorskip("h5netcdf")

from h2integrate.resource.era5_reader import ERA5SingleLevelsReader


WIND_UNITS = {
    "u10": "m s**-1",
    "v10": "m s**-1",
    "u100": "m s**-1",
    "v100": "m s**-1",
}


def _write_monthly_wind_files(
    resource_dir: Path,
    year: int = 2023,
    pattern: str = "wind_{year}_{month:02d}.nc",
) -> None:
    """Write one synthetic deterministic ERA5 wind file per month."""

    latitudes = np.array([-23.25, -23.50])
    longitudes = np.array([-68.50, -68.25])
    for month in range(1, 13):
        hours_in_month = calendar.monthrange(year, month)[1] * 24
        valid_times = pd.date_range(
            f"{year}-{month:02d}-01 00:00:00",
            periods=hours_in_month,
            freq="h",
        )
        base_values = np.arange(hours_in_month, dtype=np.float32)[:, None, None]
        spatial_offsets = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32)
        data_variables = {}
        for variable_index, (variable_name, units) in enumerate(WIND_UNITS.items()):
            data_variables[variable_name] = (
                ("valid_time", "latitude", "longitude"),
                base_values + spatial_offsets + variable_index * 1000.0,
                {"units": units},
            )

        dataset = xr.Dataset(
            data_vars=data_variables,
            coords={
                "valid_time": valid_times,
                "latitude": latitudes,
                "longitude": longitudes,
                "expver": ("valid_time", np.full(hours_in_month, "0001")),
                "number": 0,
            },
        )
        filepath = resource_dir / pattern.format(year=year, month=month)
        dataset.to_netcdf(filepath, engine="h5netcdf")


@pytest.fixture(scope="module")
def synthetic_era5_wind_directory(tmp_path_factory):
    """Create a complete synthetic annual ERA5 wind dataset."""

    resource_dir = tmp_path_factory.mktemp("era5_reader")
    _write_monthly_wind_files(resource_dir)
    return resource_dir


@pytest.mark.unit
def test_resolve_monthly_files_uses_configurable_pattern(synthetic_era5_wind_directory):
    reader = ERA5SingleLevelsReader(
        resource_dir=synthetic_era5_wind_directory,
        resource_year=2023,
        file_patterns={"wind": "wind_{year}_{month:02d}.nc"},
    )

    monthly_files = reader.resolve_monthly_files("wind")

    assert len(monthly_files) == 12
    assert monthly_files[0].name == "wind_2023_01.nc"
    assert monthly_files[-1].name == "wind_2023_12.nc"


@pytest.mark.unit
def test_read_site_returns_validated_annual_nearest_series(synthetic_era5_wind_directory):
    reader = ERA5SingleLevelsReader(
        resource_dir=synthetic_era5_wind_directory,
        resource_year=2023,
        file_patterns={"wind": "wind_{year}_{month:02d}.nc"},
    )

    dataset = reader.read_site(
        latitude=-23.45,
        longitude=-68.30,
        categories=["wind"],
    )

    assert dataset.sizes == {"valid_time": 8760}
    assert set(WIND_UNITS) <= set(dataset.data_vars)
    assert dataset["valid_time"].values[0] == np.datetime64("2023-01-01T00:00:00")
    assert dataset["valid_time"].values[-1] == np.datetime64("2023-12-31T23:00:00")
    assert dataset.attrs["selected_latitude"] == pytest.approx(-23.50)
    assert dataset.attrs["selected_longitude"] == pytest.approx(-68.25)
    assert dataset.attrs["requested_latitude"] == pytest.approx(-23.45)
    assert dataset.attrs["requested_longitude"] == pytest.approx(-68.30)
    assert dataset.attrs["spatial_method"] == "nearest"
    assert dataset.attrs["grid_distance_km"] < 15.0
    assert dataset.attrs["expver_values"] == ("0001",)
    assert dataset.attrs["number"] == 0
    assert len(dataset.attrs["source_files"]) == 12
    np.testing.assert_allclose(dataset["u10"].values[:2], [3.0, 4.0])


@pytest.mark.unit
def test_read_site_warns_when_nearest_point_exceeds_configured_distance(
    synthetic_era5_wind_directory,
):
    reader = ERA5SingleLevelsReader(
        resource_dir=synthetic_era5_wind_directory,
        resource_year=2023,
        file_patterns={"wind": "wind_{year}_{month:02d}.nc"},
        nearest_distance_warning_km=1.0,
    )

    with pytest.warns(UserWarning, match="results represent the ERA5 grid cell"):
        dataset = reader.read_site(
            latitude=-23.45,
            longitude=-68.30,
            categories=["wind"],
        )

    assert dataset.attrs["nearest_distance_warning_km"] == 1.0


@pytest.mark.unit
def test_read_site_rejects_location_outside_domain(synthetic_era5_wind_directory):
    reader = ERA5SingleLevelsReader(
        resource_dir=synthetic_era5_wind_directory,
        resource_year=2023,
        file_patterns={"wind": "wind_{year}_{month:02d}.nc"},
    )

    with pytest.raises(ValueError, match="outside ERA5 domain"):
        reader.read_site(
            latitude=-30.0,
            longitude=-68.25,
            categories=["wind"],
        )


@pytest.mark.unit
def test_resolve_monthly_files_reports_missing_month(tmp_path):
    for month in range(1, 12):
        (tmp_path / f"wind_2023_{month:02d}.nc").touch()

    reader = ERA5SingleLevelsReader(
        resource_dir=tmp_path,
        resource_year=2023,
        file_patterns={"wind": "wind_{year}_{month:02d}.nc"},
    )

    with pytest.raises(FileNotFoundError, match="wind_2023_12.nc"):
        reader.resolve_monthly_files("wind")


@pytest.mark.unit
def test_annual_validation_rejects_non_hourly_time(tmp_path):
    reader = ERA5SingleLevelsReader(resource_dir=tmp_path, resource_year=2023)
    dataset = xr.Dataset(
        coords={
            "valid_time": pd.DatetimeIndex(
                ["2023-01-01 00:00:00", "2023-01-01 02:00:00"]
            )
        }
    )

    with pytest.raises(ValueError, match="continuous at hourly resolution"):
        reader._validate_annual_time(dataset, n_timesteps=2)
