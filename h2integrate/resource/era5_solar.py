"""Common solar transformations for ERA5 Single Levels point datasets."""

from __future__ import annotations

import importlib
import warnings
from typing import Any

import numpy as np
import pandas as pd

from h2integrate.resource.era5_reader import ERA5_EXPECTED_UNITS, ERA5_TIME_DIMENSION
from h2integrate.resource.era5_wind import (
    KELVIN_OFFSET_C,
    STANDARD_GRAVITY_M_PER_S2,
    wind_components_to_speed_and_direction,
)


PASCALS_PER_MILLIBAR = 100.0
HOURLY_ACCUMULATION_SECONDS = 3600.0
SOLAR_GEOMETRY_OFFSET_MINUTES = 30
DEFAULT_MAXIMUM_ZENITH_ANGLE_DEG = 88.0

ERA5_SOLAR_TRANSFORMATION_VARIABLES = (
    "ssrd",
    "fdir",
    "t2m",
    "d2m",
    "sp",
    "z",
    "u10",
    "v10",
)


def _import_pvlib() -> Any:
    """Import pvlib with an actionable error for base installations."""

    try:
        return importlib.import_module("pvlib")
    except ImportError as error:
        raise ImportError(
            "ERA5 solar transformations require optional dependencies. "
            "Install them with the era5 project extra."
        ) from error


def transform_era5_solar_dataset(
    dataset: Any,
    site_elevation_m: float | None = None,
    maximum_zenith_angle_deg: float = DEFAULT_MAXIMUM_ZENITH_ANGLE_DEG,
) -> dict[str, Any]:
    """Transform one annual ERA5 point dataset into ``solar_resource_data``.

    The input must be the hourly UTC point dataset returned by
    :class:`~h2integrate.resource.era5_reader.ERA5SingleLevelsReader` for the
    ``solar``, ``wind``, and ``auxiliary`` categories. Radiation accumulations
    are interpreted over the hour ending at ``valid_time``. Solar position is
    evaluated 30 minutes earlier, at the center of that accumulation period.

    Args:
        dataset: Annual xarray-like point dataset containing the required ERA5
            solar and meteorological variables.
        site_elevation_m: Optional configured site elevation in m. When supplied,
            it takes precedence over ERA5 elevation while preserving the latter
            as provenance.
        maximum_zenith_angle_deg: Zenith angle at or above which DNI is set to
            zero to avoid unstable division near the horizon. Defaults to 88°.

    Returns:
        Dictionary compatible with H2Integrate's ``solar_resource_data`` contract.

    Raises:
        ValueError: If required variables, units, dimensions, timestamps, physical
            limits, elevation, or the zenith threshold are invalid.
    """

    valid_time = _validate_solar_dataset(dataset)
    maximum_zenith_angle_deg = float(maximum_zenith_angle_deg)
    if not 0.0 < maximum_zenith_angle_deg < 90.0:
        raise ValueError("maximum_zenith_angle_deg must be between 0 and 90 degrees.")

    ssrd_j_per_m2 = np.asarray(dataset["ssrd"].values, dtype=float)
    fdir_j_per_m2 = np.asarray(dataset["fdir"].values, dtype=float)
    temperature_kelvin = np.asarray(dataset["t2m"].values, dtype=float)
    dew_point_kelvin = np.asarray(dataset["d2m"].values, dtype=float)
    pressure_pa = np.asarray(dataset["sp"].values, dtype=float)
    geopotential_m2_per_s2 = np.asarray(dataset["z"].values, dtype=float)

    if np.any(ssrd_j_per_m2 < 0.0) or np.any(fdir_j_per_m2 < 0.0):
        raise ValueError("ERA5 ssrd and fdir accumulations must be nonnegative.")
    if np.any(temperature_kelvin < 0.0) or np.any(dew_point_kelvin < 0.0):
        raise ValueError("ERA5 t2m and d2m cannot be below absolute zero.")
    if np.any(dew_point_kelvin > temperature_kelvin + 0.1):
        raise ValueError("ERA5 d2m cannot exceed t2m by more than 0.1 K.")
    if np.any(pressure_pa <= 0.0):
        raise ValueError("ERA5 sp must contain strictly positive pressure values.")

    fdir_exceeds_ssrd = fdir_j_per_m2 > ssrd_j_per_m2
    fdir_exceeds_ssrd_count = int(np.count_nonzero(fdir_exceeds_ssrd))
    if fdir_exceeds_ssrd_count:
        warnings.warn(
            (
                f"ERA5 fdir exceeds ssrd in {fdir_exceeds_ssrd_count} timestep(s); "
                "direct horizontal irradiance was limited to GHI."
            ),
            UserWarning,
            stacklevel=2,
        )
    bounded_fdir_j_per_m2 = np.minimum(fdir_j_per_m2, ssrd_j_per_m2)
    ghi_w_per_m2 = ssrd_j_per_m2 / HOURLY_ACCUMULATION_SECONDS
    direct_horizontal_w_per_m2 = bounded_fdir_j_per_m2 / HOURLY_ACCUMULATION_SECONDS
    dhi_w_per_m2 = np.maximum(ghi_w_per_m2 - direct_horizontal_w_per_m2, 0.0)

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

    selected_latitude = _site_coordinate(dataset, "latitude")
    selected_longitude = _site_coordinate(dataset, "longitude")
    geometry_time = valid_time.tz_localize("UTC") - pd.Timedelta(
        minutes=SOLAR_GEOMETRY_OFFSET_MINUTES
    )
    pvlib = _import_pvlib()
    solar_position = pvlib.solarposition.get_solarposition(
        geometry_time,
        latitude=selected_latitude,
        longitude=selected_longitude,
        altitude=elevation_m,
    )
    solar_zenith_angle_deg = solar_position["zenith"].to_numpy(dtype=float)
    cosine_zenith = np.cos(np.radians(solar_zenith_angle_deg))
    stable_dni = (
        (solar_zenith_angle_deg < maximum_zenith_angle_deg)
        & (cosine_zenith > 0.0)
        & (direct_horizontal_w_per_m2 > 0.0)
    )
    dni_w_per_m2 = np.zeros_like(direct_horizontal_w_per_m2)
    dni_w_per_m2[stable_dni] = (
        direct_horizontal_w_per_m2[stable_dni] / cosine_zenith[stable_dni]
    )
    dni_zeroed_by_zenith_count = int(
        np.count_nonzero((direct_horizontal_w_per_m2 > 0.0) & ~stable_dni)
    )

    wind_speed_m_per_s, wind_direction_deg = wind_components_to_speed_and_direction(
        dataset["u10"].values,
        dataset["v10"].values,
    )
    start_time = valid_time[0].strftime("%Y/%m/%d %H:%M:%S")
    end_time = valid_time[-1].strftime("%Y/%m/%d %H:%M:%S")

    solar_resource_data: dict[str, Any] = {
        "ghi": ghi_w_per_m2,
        "dhi": dhi_w_per_m2,
        "dni": dni_w_per_m2,
        "solar_zenith_angle": solar_zenith_angle_deg,
        "temperature": temperature_kelvin - KELVIN_OFFSET_C,
        "dew_point": dew_point_kelvin - KELVIN_OFFSET_C,
        "pressure": pressure_pa / PASCALS_PER_MILLIBAR,
        "wind_speed": wind_speed_m_per_s,
        "wind_direction": wind_direction_deg,
        "year": valid_time.year.to_numpy(dtype=float),
        "month": valid_time.month.to_numpy(dtype=float),
        "day": valid_time.day.to_numpy(dtype=float),
        "hour": valid_time.hour.to_numpy(dtype=float),
        "minute": valid_time.minute.to_numpy(dtype=float),
        "data_tz": 0.0,
        "dt": int(HOURLY_ACCUMULATION_SECONDS),
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
            for variable_name in ERA5_SOLAR_TRANSFORMATION_VARIABLES
        },
        "accumulation_period_seconds": int(HOURLY_ACCUMULATION_SECONDS),
        "solar_geometry_time_offset_seconds": -SOLAR_GEOMETRY_OFFSET_MINUTES * 60,
        "maximum_zenith_angle_deg": maximum_zenith_angle_deg,
        "fdir_exceeds_ssrd_count": fdir_exceeds_ssrd_count,
        "dni_zeroed_by_zenith_count": dni_zeroed_by_zenith_count,
        "transformations": (
            "ghi_W_per_m2=ssrd_J_per_m2/3600",
            "bhi_W_per_m2=min(fdir,ssrd)_J_per_m2/3600",
            "dhi_W_per_m2=max(ghi-bhi,0)",
            "dni_W_per_m2=bhi/cos(true_zenith_at_valid_time_minus_30_minutes)",
            "temperature_degC=t2m_K-273.15",
            "dew_point_degC=d2m_K-273.15",
            "pressure_mbar=sp_Pa/100",
            "era5_elevation_m=z/9.80665",
            "wind_speed=hypot(u10,v10)",
            "wind_direction=(270-degrees(atan2(v10,u10)))%360",
        ),
    }
    _copy_reader_provenance(dataset, solar_resource_data)
    return solar_resource_data


def _validate_solar_dataset(dataset: Any) -> pd.DatetimeIndex:
    """Validate the point dataset required by the solar transformation."""

    if ERA5_TIME_DIMENSION not in dataset.coords:
        raise ValueError(f"ERA5 solar dataset is missing {ERA5_TIME_DIMENSION!r}.")
    if dataset.attrs.get("data_timezone") != "UTC":
        raise ValueError("ERA5 solar dataset must explicitly declare data_timezone='UTC'.")
    missing_variables = set(ERA5_SOLAR_TRANSFORMATION_VARIABLES).difference(dataset.data_vars)
    if missing_variables:
        raise ValueError(
            "ERA5 solar transformation is missing variables: "
            f"{', '.join(sorted(missing_variables))}."
        )

    valid_time = pd.DatetimeIndex(dataset[ERA5_TIME_DIMENSION].values)
    if valid_time.empty:
        raise ValueError("ERA5 solar dataset must contain at least one hourly timestep.")
    if valid_time.has_duplicates or not valid_time.is_monotonic_increasing:
        raise ValueError("ERA5 solar valid_time must be strictly increasing without duplicates.")
    if len(valid_time) > 1 and not np.all(np.diff(valid_time.asi8) == pd.Timedelta(hours=1).value):
        raise ValueError("ERA5 solar valid_time must be continuous at hourly resolution.")

    for variable_name in ERA5_SOLAR_TRANSFORMATION_VARIABLES:
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
        f"ERA5 solar dataset does not identify one selected {coordinate_name} coordinate."
    )


def _copy_reader_provenance(dataset: Any, solar_resource_data: dict[str, Any]) -> None:
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
            solar_resource_data[attribute_name] = dataset.attrs[attribute_name]
