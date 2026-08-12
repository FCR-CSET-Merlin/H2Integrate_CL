"""Common wind transformations for ERA5 Single Levels point datasets."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from h2integrate.resource.era5_reader import ERA5_EXPECTED_UNITS, ERA5_TIME_DIMENSION


STANDARD_ATMOSPHERE_PA = 101_325.0
STANDARD_GRAVITY_M_PER_S2 = 9.80665
KELVIN_OFFSET_C = 273.15

ERA5_WIND_TRANSFORMATION_VARIABLES = (
    "u10",
    "v10",
    "u100",
    "v100",
    "t2m",
    "sp",
    "z",
)


def wind_components_to_speed_and_direction(
    u_component_m_per_s: Any,
    v_component_m_per_s: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert horizontal wind components to speed and meteorological direction.

    Direction is expressed clockwise from true north and identifies the direction
    from which the wind blows. For a calm sample (``u == v == 0``), the formula
    deterministically returns 270 degrees; direction has no physical meaning when
    wind speed is zero.

    Args:
        u_component_m_per_s: Eastward wind component in m/s.
        v_component_m_per_s: Northward wind component in m/s.

    Returns:
        Wind speed in m/s and meteorological direction in degrees.
    """

    u_component = np.asarray(u_component_m_per_s, dtype=float)
    v_component = np.asarray(v_component_m_per_s, dtype=float)
    if u_component.shape != v_component.shape:
        raise ValueError("ERA5 u and v wind components must have identical shapes.")
    if not np.all(np.isfinite(u_component)) or not np.all(np.isfinite(v_component)):
        raise ValueError("ERA5 wind components must contain only finite values.")

    wind_speed = np.hypot(u_component, v_component)
    wind_direction = (270.0 - np.degrees(np.arctan2(v_component, u_component))) % 360.0
    return wind_speed, wind_direction


def transform_era5_wind_dataset(
    dataset: Any,
    site_elevation_m: float | None = None,
) -> dict[str, Any]:
    """Transform one annual ERA5 point dataset into ``wind_resource_data``.

    The input must be the hourly UTC point dataset returned by
    :class:`~h2integrate.resource.era5_reader.ERA5SingleLevelsReader` for the
    ``wind`` and ``auxiliary`` categories. SI source variables are converted only
    at the existing H2Integrate/PySAM interface: temperature from K to degrees C,
    pressure from Pa to standard atmospheres, and geopotential to elevation in m.

    Args:
        dataset: Annual xarray-like point dataset with ``valid_time`` and all
            variables listed in ``ERA5_WIND_TRANSFORMATION_VARIABLES``.
        site_elevation_m: Optional configured site elevation in m. When supplied,
            it takes precedence over ERA5 elevation while the latter is retained
            as ``era5_elevation`` metadata.

    Returns:
        Dictionary compatible with H2Integrate's ``wind_resource_data`` contract.

    Raises:
        ValueError: If required variables, units, dimensions, time data, or
            physically constrained values are invalid.
    """

    valid_time = _validate_wind_dataset(dataset)
    u10 = np.asarray(dataset["u10"].values, dtype=float)
    v10 = np.asarray(dataset["v10"].values, dtype=float)
    u100 = np.asarray(dataset["u100"].values, dtype=float)
    v100 = np.asarray(dataset["v100"].values, dtype=float)
    temperature_kelvin = np.asarray(dataset["t2m"].values, dtype=float)
    pressure_pa = np.asarray(dataset["sp"].values, dtype=float)
    geopotential_m2_per_s2 = np.asarray(dataset["z"].values, dtype=float)

    if np.any(temperature_kelvin < 0.0):
        raise ValueError("ERA5 t2m contains temperatures below absolute zero.")
    if np.any(pressure_pa <= 0.0):
        raise ValueError("ERA5 sp must contain strictly positive pressure values.")

    wind_speed_10m, wind_direction_10m = wind_components_to_speed_and_direction(u10, v10)
    wind_speed_100m, wind_direction_100m = wind_components_to_speed_and_direction(u100, v100)

    if not np.allclose(
        geopotential_m2_per_s2,
        geopotential_m2_per_s2[0],
        rtol=0.0,
        atol=1.0e-3,
    ):
        raise ValueError("ERA5 surface geopotential z must remain constant through the year.")
    era5_elevation_m = float(np.mean(geopotential_m2_per_s2) / STANDARD_GRAVITY_M_PER_S2)

    if site_elevation_m is None:
        elevation_m = era5_elevation_m
        elevation_source = "ERA5_geopotential"
    else:
        elevation_m = float(site_elevation_m)
        if not np.isfinite(elevation_m):
            raise ValueError("site_elevation_m must be finite when provided.")
        elevation_source = "configured_site"

    start_time = valid_time[0].strftime("%Y/%m/%d %H:%M:%S")
    end_time = valid_time[-1].strftime("%Y/%m/%d %H:%M:%S")
    selected_latitude = _site_coordinate(dataset, "latitude")
    selected_longitude = _site_coordinate(dataset, "longitude")

    wind_resource_data: dict[str, Any] = {
        "wind_speed_10m": wind_speed_10m,
        "wind_direction_10m": wind_direction_10m,
        "wind_speed_100m": wind_speed_100m,
        "wind_direction_100m": wind_direction_100m,
        "temperature_2m": temperature_kelvin - KELVIN_OFFSET_C,
        "pressure_0m": pressure_pa / STANDARD_ATMOSPHERE_PA,
        "year": valid_time.year.to_numpy(dtype=float),
        "month": valid_time.month.to_numpy(dtype=float),
        "day": valid_time.day.to_numpy(dtype=float),
        "hour": valid_time.hour.to_numpy(dtype=float),
        "minute": valid_time.minute.to_numpy(dtype=float),
        "data_tz": 0.0,
        "dt": 3600,
        "start_time": f"{start_time} (+0000)",
        "end_time": f"{end_time} (+0000)",
        "site_lat": selected_latitude,
        "site_lon": selected_longitude,
        "elevation": elevation_m,
        "era5_elevation": era5_elevation_m,
        "elevation_source": elevation_source,
        "dataset": dataset.attrs.get("dataset", "ERA5 Single Levels"),
        "resource_year": int(dataset.attrs.get("resource_year", valid_time[0].year)),
        "data_timezone": "UTC",
        "source_files": tuple(dataset.attrs.get("source_files", ())),
        "source_units": {
            variable_name: dataset[variable_name].attrs["units"]
            for variable_name in ERA5_WIND_TRANSFORMATION_VARIABLES
        },
        "transformations": (
            "wind_speed=hypot(u,v)",
            "wind_direction=(270-degrees(atan2(v,u)))%360",
            "temperature_degC=t2m_K-273.15",
            "pressure_atm=sp_Pa/101325",
            "era5_elevation_m=z/9.80665",
        ),
    }
    _copy_reader_provenance(dataset, wind_resource_data)
    return wind_resource_data


def _validate_wind_dataset(dataset: Any) -> pd.DatetimeIndex:
    """Validate the point dataset required by the wind transformation."""

    if ERA5_TIME_DIMENSION not in dataset.coords:
        raise ValueError(f"ERA5 wind dataset is missing {ERA5_TIME_DIMENSION!r}.")
    if dataset.attrs.get("data_timezone") != "UTC":
        raise ValueError("ERA5 wind dataset must explicitly declare data_timezone='UTC'.")
    missing_variables = set(ERA5_WIND_TRANSFORMATION_VARIABLES).difference(dataset.data_vars)
    if missing_variables:
        raise ValueError(
            "ERA5 wind transformation is missing variables: "
            f"{', '.join(sorted(missing_variables))}."
        )

    valid_time = pd.DatetimeIndex(dataset[ERA5_TIME_DIMENSION].values)
    if valid_time.empty:
        raise ValueError("ERA5 wind dataset must contain at least one hourly timestep.")
    if valid_time.has_duplicates or not valid_time.is_monotonic_increasing:
        raise ValueError("ERA5 wind valid_time must be strictly increasing without duplicates.")
    if len(valid_time) > 1 and not np.all(np.diff(valid_time.asi8) == pd.Timedelta(hours=1).value):
        raise ValueError("ERA5 wind valid_time must be continuous at hourly resolution.")

    for variable_name in ERA5_WIND_TRANSFORMATION_VARIABLES:
        variable = dataset[variable_name]
        if variable.dims != (ERA5_TIME_DIMENSION,):
            raise ValueError(
                f"ERA5 {variable_name} dimensions are {variable.dims}; "
                f"expected ({ERA5_TIME_DIMENSION!r},)."
            )
        if variable.sizes[ERA5_TIME_DIMENSION] != len(valid_time):
            raise ValueError(f"ERA5 {variable_name} length differs from valid_time.")
        units = variable.attrs.get("units")
        if units not in ERA5_EXPECTED_UNITS[variable_name]:
            raise ValueError(
                f"ERA5 {variable_name} has units {units!r}; "
                f"expected one of {sorted(ERA5_EXPECTED_UNITS[variable_name])}."
            )
        if not np.all(np.isfinite(variable.values)):
            raise ValueError(f"ERA5 {variable_name} contains missing or non-finite values.")
    return valid_time


def _site_coordinate(dataset: Any, coordinate_name: str) -> float:
    """Return the selected point coordinate, preferring reader provenance."""

    attribute_name = f"selected_{coordinate_name}"
    if attribute_name in dataset.attrs:
        return float(dataset.attrs[attribute_name])
    if coordinate_name in dataset.coords and dataset[coordinate_name].size == 1:
        return float(dataset[coordinate_name].item())
    raise ValueError(
        f"ERA5 wind dataset does not identify one selected {coordinate_name} coordinate."
    )


def _copy_reader_provenance(dataset: Any, wind_resource_data: dict[str, Any]) -> None:
    """Copy reader metadata relevant to reproducibility when present."""

    provenance_attributes = (
        "requested_latitude",
        "requested_longitude",
        "selected_latitude",
        "selected_longitude",
        "grid_distance_km",
        "spatial_method",
        "nearest_distance_warning_km",
        "categories",
        "expver_values",
        "number",
    )
    for attribute_name in provenance_attributes:
        if attribute_name in dataset.attrs:
            wind_resource_data[attribute_name] = dataset.attrs[attribute_name]
