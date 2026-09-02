"""Tests for the optional ERA5 dependency stack."""

from pathlib import Path
import tomllib

import numpy as np
import pandas as pd
import pytest


@pytest.mark.unit
def test_era5_optional_dependencies_are_declared():
    """Verify that the ERA5 extra declares the required libraries."""

    repository_root = Path(__file__).resolve().parents[3]
    with (repository_root / "pyproject.toml").open("rb") as stream:
        project_configuration = tomllib.load(stream)

    era5_dependencies = set(
        project_configuration["project"]["optional-dependencies"]["era5"]
    )

    assert era5_dependencies == {"h5netcdf", "pvlib", "xarray"}


@pytest.mark.unit
def test_era5_dependency_stack_can_roundtrip_netcdf(tmp_path):
    """Verify that xarray can write and reopen NetCDF4 through h5netcdf."""

    h5netcdf = pytest.importorskip("h5netcdf")
    xarray = pytest.importorskip("xarray")

    assert h5netcdf is not None

    valid_times = pd.date_range(
        "2023-01-01 00:00:00",
        periods=2,
        freq="h",
        tz=None,
    )
    source_dataset = xarray.Dataset(
        data_vars={
            "ssrd": (
                ("valid_time", "latitude", "longitude"),
                np.array([[[0.0]], [[3_600_000.0]]], dtype=np.float32),
                {"units": "J m**-2"},
            )
        },
        coords={
            "valid_time": valid_times,
            "latitude": np.array([-23.5]),
            "longitude": np.array([-68.25]),
        },
    )
    netcdf_path = tmp_path / "era5_dependency_smoke_test.nc"

    source_dataset.to_netcdf(netcdf_path, engine="h5netcdf")

    with xarray.open_dataset(netcdf_path, engine="h5netcdf") as loaded_dataset:
        assert loaded_dataset.sizes == {
            "valid_time": 2,
            "latitude": 1,
            "longitude": 1,
        }
        assert loaded_dataset["ssrd"].attrs["units"] == "J m**-2"
        np.testing.assert_allclose(
            loaded_dataset["ssrd"].values,
            source_dataset["ssrd"].values,
        )


@pytest.mark.unit
def test_pvlib_can_calculate_solar_position():
    """Verify that pvlib can calculate solar position for a Chilean site."""

    pvlib = pytest.importorskip("pvlib")

    valid_times = pd.DatetimeIndex(["2023-06-21T16:00:00Z"])
    solar_position = pvlib.solarposition.get_solarposition(
        valid_times,
        latitude=-23.5,
        longitude=-68.25,
    )

    apparent_zenith_degrees = float(solar_position["apparent_zenith"].iloc[0])
    assert 0.0 <= apparent_zenith_degrees <= 90.0
