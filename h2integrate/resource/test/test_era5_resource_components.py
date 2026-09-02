"""Tests for ERA5 Single Levels OpenMDAO resource components."""

import calendar
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import openmdao.api as om


xr = pytest.importorskip("xarray")
pytest.importorskip("h5netcdf")
pvlib = pytest.importorskip("pvlib")

from h2integrate.core.h2integrate_model import H2IntegrateModel
from h2integrate.core.supported_models import supported_models
from h2integrate.resource.era5_resource import (
    ERA5SingleLevelsSolarResource,
    ERA5SingleLevelsWindResource,
)
from h2integrate.converters.wind.wind_plant_baseclass import WindPerformanceBaseClass


ERA5_CATEGORY_VARIABLES = {
    "wind": {
        "u10": (3.0, "m s**-1"),
        "v10": (4.0, "m s**-1"),
        "u100": (6.0, "m s**-1"),
        "v100": (8.0, "m s**-1"),
    },
    "solar": {
        "ssrd": (3_600_000.0, "J m**-2"),
        "fdir": (1_800_000.0, "J m**-2"),
    },
    "auxiliary": {
        "t2m": (293.15, "K"),
        "d2m": (283.15, "K"),
        "sp": (90_000.0, "Pa"),
        "z": (9_806.65, "m**2 s**-2"),
    },
}


ERA5_HYBRID_CONFIG_DIRECTORY = Path(__file__).parent / "era5_hybrid_config"
ERA5_RESOURCE_DIRECTORY_PLACEHOLDER = "__ERA5_RESOURCE_DIR__"


def _write_annual_era5_files(resource_dir: Path, year: int = 2023) -> None:
    """Write synthetic monthly NetCDF files for all ERA5 categories."""

    latitudes = np.array([-23.25, -23.50])
    longitudes = np.array([-68.50, -68.25])
    spatial_offsets = np.array([[0.0, 0.1], [0.2, 0.3]], dtype=np.float32)
    for category, variables in ERA5_CATEGORY_VARIABLES.items():
        for month in range(1, 13):
            hours_in_month = calendar.monthrange(year, month)[1] * 24
            valid_time = pd.date_range(
                f"{year}-{month:02d}-01 00:00:00",
                periods=hours_in_month,
                freq="h",
            )
            solar_position = pvlib.solarposition.get_solarposition(
                valid_time.tz_localize("UTC") - pd.Timedelta(minutes=30),
                latitude=-23.50,
                longitude=-68.25,
                altitude=1_250.0,
            )
            cosine_zenith = np.clip(
                np.cos(np.deg2rad(solar_position["zenith"].to_numpy())),
                0.0,
                1.0,
            )
            data_variables = {}
            for variable_name, (base_value, units) in variables.items():
                if variable_name == "z":
                    variable_values = np.full(
                        (hours_in_month, 2, 2),
                        base_value,
                        dtype=np.float32,
                    )
                elif variable_name in {"ssrd", "fdir"}:
                    peak_irradiance = 800.0 if variable_name == "ssrd" else 600.0
                    accumulated_irradiance = peak_irradiance * cosine_zenith * 3600.0
                    variable_values = np.broadcast_to(
                        accumulated_irradiance[:, np.newaxis, np.newaxis],
                        (hours_in_month, 2, 2),
                    ).astype(np.float32)
                else:
                    variable_values = np.broadcast_to(
                        base_value + spatial_offsets,
                        (hours_in_month, 2, 2),
                    ).copy()
                data_variables[variable_name] = (
                    ("valid_time", "latitude", "longitude"),
                    variable_values,
                    {"units": units},
                )

            dataset = xr.Dataset(
                data_vars=data_variables,
                coords={
                    "valid_time": valid_time,
                    "latitude": latitudes,
                    "longitude": longitudes,
                    "expver": ("valid_time", np.full(hours_in_month, "0001")),
                    "number": 0,
                },
            )
            filepath = resource_dir / f"era5_chile_{category}_{year}_{month:02d}.nc"
            dataset.to_netcdf(filepath, engine="h5netcdf")


@pytest.fixture(scope="module")
def synthetic_era5_component_directory(tmp_path_factory):
    """Create complete synthetic inputs shared by component tests."""

    resource_dir = tmp_path_factory.mktemp("era5_components")
    _write_annual_era5_files(resource_dir)
    return resource_dir

@pytest.fixture(scope="module")
def era5_hybrid_config_file(
    tmp_path_factory,
    synthetic_era5_component_directory,
):
    """Materialize the YAML configuration with a temporary ERA5 resource path."""

    runtime_config_directory = tmp_path_factory.mktemp("era5_hybrid_config")
    shutil.copytree(
        ERA5_HYBRID_CONFIG_DIRECTORY,
        runtime_config_directory,
        dirs_exist_ok=True,
    )
    plant_config_path = runtime_config_directory / "plant_config.yaml"
    plant_config_text = plant_config_path.read_text(encoding="utf-8")
    assert plant_config_text.count(ERA5_RESOURCE_DIRECTORY_PLACEHOLDER) == 2
    plant_config_path.write_text(
        plant_config_text.replace(
            ERA5_RESOURCE_DIRECTORY_PLACEHOLDER,
            str(synthetic_era5_component_directory),
        ),
        encoding="utf-8",
    )
    return runtime_config_directory / "era5_hybrid.yaml"



def _plant_config(
    *,
    latitude: float = -23.45,
    longitude: float = -68.30,
    elevation_m: float = 1_250.0,
    dt_seconds: int = 3600,
    timezone: float = 0.0,
) -> dict:
    """Return the plant configuration shape expected by resource components."""

    return {
        "site": {
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation_m,
        },
        "plant": {
            "simulation": {
                "dt": dt_seconds,
                "n_timesteps": 8760,
                "timezone": timezone,
            }
        },
    }


def _run_resource_component(component_class, plant_config, resource_config):
    """Set up and execute one ERA5 resource component."""

    problem = om.Problem(reports=False)
    component = component_class(
        plant_config=plant_config,
        resource_config=resource_config,
        driver_config={},
    )
    problem.model.add_subsystem("resource", component)
    problem.setup()
    problem.run_model()
    return problem


@pytest.mark.unit
def test_era5_resource_models_are_registered():
    assert supported_models["ERA5SingleLevelsWindResource"] is ERA5SingleLevelsWindResource
    assert supported_models["ERA5SingleLevelsSolarResource"] is ERA5SingleLevelsSolarResource


@pytest.mark.unit
def test_wind_component_outputs_existing_resource_contract(
    synthetic_era5_component_directory,
):
    problem = _run_resource_component(
        ERA5SingleLevelsWindResource,
        _plant_config(),
        {
            "resource_year": 2023,
            "resource_dir": synthetic_era5_component_directory,
        },
    )

    resource_data = problem.get_val("resource.wind_resource_data")
    assert len(resource_data["wind_speed_100m"]) == 8760
    assert resource_data["selected_latitude"] == pytest.approx(-23.50)
    assert resource_data["selected_longitude"] == pytest.approx(-68.25)
    assert resource_data["elevation"] == pytest.approx(1_250.0)
    assert resource_data["era5_elevation"] == pytest.approx(1_000.0)
    assert resource_data["elevation_source"] == "configured_site"
    assert resource_data["dt"] == 3600
    assert resource_data["data_tz"] == 0.0


@pytest.mark.unit
def test_solar_component_outputs_existing_resource_contract(
    synthetic_era5_component_directory,
):
    problem = _run_resource_component(
        ERA5SingleLevelsSolarResource,
        _plant_config(),
        {
            "resource_year": 2023,
            "resource_dir": synthetic_era5_component_directory,
            "maximum_zenith_angle_deg": 87.0,
        },
    )

    resource_data = problem.get_val("resource.solar_resource_data")
    assert len(resource_data["ghi"]) == 8760
    assert len(resource_data["dni"]) == 8760
    assert np.isfinite(resource_data["dni"]).all()
    assert resource_data["maximum_zenith_angle_deg"] == pytest.approx(87.0)
    assert resource_data["elevation"] == pytest.approx(1_250.0)
    assert resource_data["pressure"][0] == pytest.approx(900.003)


@pytest.mark.unit
def test_variable_location_reloads_nearest_grid_point(
    synthetic_era5_component_directory,
):
    problem = _run_resource_component(
        ERA5SingleLevelsWindResource,
        _plant_config(),
        {
            "resource_year": 2023,
            "resource_dir": synthetic_era5_component_directory,
            "use_fixed_resource_location": False,
        },
    )
    initial_data = problem.get_val("resource.wind_resource_data")
    initial_speed = float(initial_data["wind_speed_10m"][0])

    problem.set_val("resource.latitude", -23.26, units="deg")
    problem.set_val("resource.longitude", -68.49, units="deg")
    problem.run_model()
    updated_data = problem.get_val("resource.wind_resource_data")

    assert updated_data["selected_latitude"] == pytest.approx(-23.25)
    assert updated_data["selected_longitude"] == pytest.approx(-68.50)
    assert float(updated_data["wind_speed_10m"][0]) != pytest.approx(initial_speed)


@pytest.mark.unit
def test_component_rejects_nonhourly_simulation(synthetic_era5_component_directory):
    component = ERA5SingleLevelsWindResource(
        plant_config=_plant_config(dt_seconds=1800),
        resource_config={
            "resource_year": 2023,
            "resource_dir": synthetic_era5_component_directory,
        },
        driver_config={},
    )
    problem = om.Problem(reports=False)
    problem.model.add_subsystem("resource", component)

    with pytest.raises(ValueError, match="requires plant simulation dt=3600 seconds"):
        problem.setup()


@pytest.mark.unit
def test_component_rejects_non_utc_simulation(synthetic_era5_component_directory):
    component = ERA5SingleLevelsSolarResource(
        plant_config=_plant_config(timezone=-4.0),
        resource_config={
            "resource_year": 2023,
            "resource_dir": synthetic_era5_component_directory,
        },
        driver_config={},
    )
    problem = om.Problem(reports=False)
    problem.model.add_subsystem("resource", component)

    with pytest.raises(ValueError, match=r"requires plant simulation timezone=0 \(UTC\)"):
        problem.setup()


@pytest.mark.unit
def test_hub_height_above_available_resource_warns_and_uses_maximum():
    resource_data = {
        "wind_speed_10m": np.ones(2),
        "wind_speed_100m": np.ones(2),
    }

    with pytest.warns(UserWarning, match="using 100 m without vertical extrapolation"):
        bounding_heights = (
            WindPerformanceBaseClass.calculate_bounding_heights_from_resource_data(
                None,
                120.0,
                resource_data,
            )
        )

    assert bounding_heights == [100]


@pytest.mark.integration
def test_h2integrate_yaml_connects_era5_wind_and_solar_to_pysam(
    era5_hybrid_config_file,
):
    """Run the YAML-defined ERA5-to-PySAM hybrid graph for one annual series."""

    model = H2IntegrateModel(era5_hybrid_config_file)
    model.run()

    wind_electricity = model.prob.get_val("wind.electricity_out", units="kW")
    solar_electricity = model.prob.get_val("solar.electricity_out", units="kW")
    combined_electricity = model.prob.get_val(
        "renewable_combiner.electricity_out",
        units="kW",
    )
    wind_resource_data = model.prob.get_val("site.wind_resource.wind_resource_data")
    solar_resource_data = model.prob.get_val("site.solar_resource.solar_resource_data")

    assert wind_electricity.shape == (8760,)
    assert solar_electricity.shape == (8760,)
    assert combined_electricity.shape == (8760,)
    assert np.isfinite(wind_electricity).all()
    assert np.isfinite(solar_electricity).all()
    assert (wind_electricity >= 0.0).all()
    assert (solar_electricity >= 0.0).all()
    assert wind_electricity.max() > 0.0
    assert solar_electricity.max() > 0.0
    np.testing.assert_allclose(
        combined_electricity,
        wind_electricity + solar_electricity,
        rtol=0.0,
        atol=1.0e-10,
    )
    assert len(wind_resource_data["year"]) == 8760
    assert len(solar_resource_data["year"]) == 8760
