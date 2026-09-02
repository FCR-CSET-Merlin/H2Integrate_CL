"""Tests for the local Sup3rWind resource component."""

from pathlib import Path

import numpy as np
import openmdao.api as om
import pandas as pd
import pytest

from h2integrate.core.supported_models import supported_models
from h2integrate.resource.wind.sup3rwind import Sup3rWindResource


def _plant_config(*, n_timesteps=24, dt=3600, timezone=0):
    return {
        "site": {"latitude": -31.070778, "longitude": -71.629250},
        "plant": {
            "simulation": {
                "n_timesteps": n_timesteps,
                "dt": dt,
                "timezone": timezone,
            }
        },
    }


def _run_resource(resource_dir: Path, filename: str, **plant_overrides):
    problem = om.Problem(reports=False)
    problem.model.add_subsystem(
        "resource",
        Sup3rWindResource(
            plant_config=_plant_config(**plant_overrides),
            resource_config={
                "resource_year": 2015,
                "resource_dir": resource_dir,
                "resource_filename": filename,
            },
            driver_config={},
        ),
    )
    problem.setup()
    problem.run_model()
    return problem.get_val("resource.wind_resource_data")


@pytest.mark.unit
def test_sup3rwind_resource_is_registered():
    assert supported_models["Sup3rWindResource"] is Sup3rWindResource


@pytest.mark.unit
def test_loads_compact_chilean_extraction(tmp_path):
    filepath = tmp_path / "sup3rwind_compact.csv"
    timestamps = pd.date_range("2015-01-01", periods=24, freq="h")
    lines = [
        "# product=Sup3rWind South America v1.0.0; frequency=60min",
        "# grid_gid=6982827",
        "# grid_latitude=-31.066666",
        "# grid_longitude=-71.633331",
        "# grid_distance_km=0.601",
        "timestamp,windspeed_100m,winddirection_100m,pressure_0m,"
        "temperature_2m,relativehumidity_2m",
    ]
    lines.extend(
        f"{timestamp:%Y-%m-%d %H:%M:%S},{6 + index / 10},180,101325,20,50"
        for index, timestamp in enumerate(timestamps)
    )
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    data = _run_resource(tmp_path, filepath.name)

    assert len(data["wind_speed_100m"]) == 24
    assert data["wind_speed_100m"][0] == pytest.approx(6.0)
    assert data["pressure_0m"][0] == pytest.approx(1.0)
    assert data["site_lat"] == pytest.approx(-31.066666)
    assert data["grid_distance_km"] == pytest.approx(0.601)
    assert data["dt"] == 3600


@pytest.mark.unit
def test_loads_wind_toolkit_style_extraction(tmp_path):
    filepath = tmp_path / "sup3rwind_wtk.csv"
    timestamps = pd.date_range("2015-01-01", periods=24, freq="h")
    lines = [
        "SiteID,42,Site Timezone,-4,Data Timezone,0,Longitude,-71.63,Latitude,-31.07",
        "Year,Month,Day,Hour,Minute,surface air pressure (Pa),"
        "air temperature at 2m (C),wind direction at 100m (deg),"
        "wind speed at 100m (m/s)",
    ]
    lines.extend(
        f"{timestamp.year},{timestamp.month},{timestamp.day},{timestamp.hour},"
        f"0,101325,20,180,{7 + index / 10}"
        for index, timestamp in enumerate(timestamps)
    )
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    data = _run_resource(tmp_path, filepath.name)

    assert np.allclose(data["pressure_0m"], 1.0)
    assert data["temperature_2m"][0] == pytest.approx(20.0)
    assert data["wind_direction_100m"][0] == pytest.approx(180.0)
    assert data["wind_speed_100m"][-1] == pytest.approx(9.3)


@pytest.mark.unit
def test_rejects_nonhourly_simulation(tmp_path):
    with pytest.raises(ValueError, match="dt=3600"):
        _run_resource(tmp_path, "missing.csv", dt=1800)


@pytest.mark.unit
def test_missing_file_does_not_attempt_download(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not download Sup3rWind"):
        _run_resource(tmp_path, "missing.csv")
