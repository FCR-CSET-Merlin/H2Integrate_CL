"""Common reader for local ERA5 Single Levels NetCDF resources."""

from __future__ import annotations

import calendar
import importlib
import math
import warnings
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_ERA5_FILE_PATTERNS = {
    "wind": "era5_chile_wind_{year}_{month:02d}.nc",
    "solar": "era5_chile_solar_{year}_{month:02d}.nc",
    "auxiliary": "era5_chile_auxiliary_{year}_{month:02d}.nc",
}

ERA5_REQUIRED_VARIABLES = {
    "wind": {"u10", "v10", "u100", "v100"},
    "solar": {"ssrd", "fdir"},
    "auxiliary": {"t2m", "d2m", "sp", "z"},
}

ERA5_EXPECTED_UNITS = {
    "u10": {"m/s", "m s**-1"},
    "v10": {"m/s", "m s**-1"},
    "u100": {"m/s", "m s**-1"},
    "v100": {"m/s", "m s**-1"},
    "ssrd": {"J/m**2", "J m**-2"},
    "fdir": {"J/m**2", "J m**-2"},
    "t2m": {"K"},
    "d2m": {"K"},
    "sp": {"Pa"},
    "z": {"m**2/s**2", "m**2 s**-2"},
}

ERA5_SPATIAL_DIMENSIONS = ("latitude", "longitude")
ERA5_TIME_DIMENSION = "valid_time"


def _import_xarray() -> Any:
    """Import xarray with an actionable error for base installations."""

    try:
        return importlib.import_module("xarray")
    except ImportError as error:
        raise ImportError(
            "ERA5 resource reading requires optional dependencies. "
            "Install them with the era5 project extra."
        ) from error


def _normalize_longitude(longitude: float, dataset_longitudes: np.ndarray) -> float:
    """Normalize a longitude to the coordinate convention used by a dataset."""

    minimum_longitude = float(np.min(dataset_longitudes))
    maximum_longitude = float(np.max(dataset_longitudes))
    if minimum_longitude >= 0.0 and longitude < 0.0:
        return longitude % 360.0
    if maximum_longitude <= 180.0 and longitude > 180.0:
        return ((longitude + 180.0) % 360.0) - 180.0
    return longitude


def _great_circle_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """Calculate great-circle distance using a mean Earth radius."""

    earth_radius_km = 6371.0088
    latitude_1_radians = math.radians(latitude_1)
    latitude_2_radians = math.radians(latitude_2)
    delta_latitude = latitude_2_radians - latitude_1_radians
    delta_longitude = math.radians(longitude_2 - longitude_1)
    haversine_value = (
        math.sin(delta_latitude / 2.0) ** 2
        + math.cos(latitude_1_radians)
        * math.cos(latitude_2_radians)
        * math.sin(delta_longitude / 2.0) ** 2
    )
    return 2.0 * earth_radius_km * math.asin(math.sqrt(haversine_value))


class ERA5SingleLevelsReader:
    """Read and validate monthly ERA5 Single Levels files for one site.

    The reader resolves configurable monthly patterns, validates deterministic
    hourly ERA5 data, selects the nearest grid point, and returns one annual
    xarray Dataset. It does not perform wind or solar transformations.

    Args:
        resource_dir: Directory containing the monthly NetCDF files.
        resource_year: Year identified by the valid_time coordinate.
        file_patterns: Mapping from category names to monthly filename patterns.
        nearest_distance_warning_km: Distance above which nearest selection
            emits a warning. Defaults to 15 km.
        include_leap_day: Whether to retain February 29 in leap years.
    """

    def __init__(
        self,
        resource_dir: str | Path,
        resource_year: int,
        file_patterns: Mapping[str, str] | None = None,
        nearest_distance_warning_km: float = 15.0,
        include_leap_day: bool = False,
    ) -> None:
        self.resource_dir = Path(resource_dir).expanduser().resolve()
        self.resource_year = int(resource_year)
        self.file_patterns = dict(DEFAULT_ERA5_FILE_PATTERNS)
        if file_patterns is not None:
            self.file_patterns.update(file_patterns)
        self.nearest_distance_warning_km = float(nearest_distance_warning_km)
        self.include_leap_day = bool(include_leap_day)

        if not self.resource_dir.is_dir():
            raise FileNotFoundError(f"ERA5 resource directory not found: {self.resource_dir}")
        if self.nearest_distance_warning_km < 0.0:
            raise ValueError("nearest_distance_warning_km must be nonnegative.")

    def resolve_monthly_files(self, category: str) -> tuple[Path, ...]:
        """Resolve and validate the twelve monthly files for a category."""

        if category not in ERA5_REQUIRED_VARIABLES:
            valid_categories = ", ".join(sorted(ERA5_REQUIRED_VARIABLES))
            raise ValueError(
                f"Unsupported ERA5 category {category!r}. Expected one of: {valid_categories}."
            )
        if category not in self.file_patterns:
            raise ValueError(f"No ERA5 filename pattern configured for category {category!r}.")

        pattern = self.file_patterns[category]
        pattern_path = Path(pattern)
        if pattern_path.is_absolute() or ".." in pattern_path.parts:
            raise ValueError(
                f"ERA5 filename pattern for {category!r} must be relative to resource_dir."
            )

        monthly_files = tuple(
            self.resource_dir
            / pattern.format(year=self.resource_year, month=month, category=category)
            for month in range(1, 13)
        )
        missing_files = [path for path in monthly_files if not path.is_file()]
        if missing_files:
            missing_names = ", ".join(path.name for path in missing_files)
            raise FileNotFoundError(
                f"Missing ERA5 {category} monthly files for {self.resource_year}: {missing_names}."
            )
        if len(set(monthly_files)) != 12:
            raise ValueError(
                f"ERA5 filename pattern for {category!r} does not resolve to 12 unique files."
            )
        return monthly_files

    def read_site(
        self,
        latitude: float,
        longitude: float,
        categories: Iterable[str],
        n_timesteps: int | None = None,
    ) -> Any:
        """Read categories and return one validated annual dataset for a site."""

        requested_categories = tuple(dict.fromkeys(categories))
        if not requested_categories:
            raise ValueError("At least one ERA5 category must be requested.")

        xarray = _import_xarray()
        category_datasets = []
        source_files: list[str] = []
        selected_latitude: float | None = None
        selected_longitude: float | None = None
        expver_values: set[str] = set()
        deterministic_number: Any = None
        reference_grid: dict[str, np.ndarray] | None = None

        for category in requested_categories:
            monthly_files = self.resolve_monthly_files(category)
            monthly_datasets = []
            for monthly_file in monthly_files:
                with xarray.open_dataset(monthly_file, engine="h5netcdf") as source_dataset:
                    self._validate_monthly_dataset(source_dataset, category, monthly_file)
                    reference_grid = self._validate_consistent_grid(
                        source_dataset, reference_grid, monthly_file
                    )
                    normalized_longitude = _normalize_longitude(
                        float(longitude),
                        np.asarray(source_dataset["longitude"].values),
                    )
                    self._validate_requested_location(
                        source_dataset,
                        float(latitude),
                        normalized_longitude,
                    )
                    selected_dataset = source_dataset.sel(
                        latitude=float(latitude),
                        longitude=normalized_longitude,
                        method="nearest",
                    ).load()
                    self._validate_selected_data(selected_dataset, category, monthly_file)
                    monthly_datasets.append(selected_dataset)
                    source_files.append(str(monthly_file))

                    current_latitude = float(selected_dataset["latitude"].item())
                    current_longitude = float(selected_dataset["longitude"].item())
                    if selected_latitude is None:
                        selected_latitude = current_latitude
                        selected_longitude = current_longitude
                    elif not (
                        math.isclose(selected_latitude, current_latitude, abs_tol=1e-9)
                        and math.isclose(selected_longitude, current_longitude, abs_tol=1e-9)
                    ):
                        raise ValueError(
                            "ERA5 monthly files or categories selected inconsistent grid points."
                        )

                    expver_values.update(
                        str(value) for value in np.unique(selected_dataset["expver"].values)
                    )
                    current_number = selected_dataset["number"].item()
                    if deterministic_number is None:
                        deterministic_number = current_number
                    elif deterministic_number != current_number:
                        raise ValueError("ERA5 deterministic member number is inconsistent.")

            category_dataset = xarray.concat(
                monthly_datasets,
                dim=ERA5_TIME_DIMENSION,
                data_vars="minimal",
                coords="minimal",
                compat="equals",
                combine_attrs="drop_conflicts",
            )
            category_datasets.append(category_dataset)

        annual_dataset = xarray.merge(
            category_datasets,
            compat="equals",
            combine_attrs="drop_conflicts",
        )
        annual_dataset = self._validate_annual_time(annual_dataset, n_timesteps)

        assert selected_latitude is not None
        assert selected_longitude is not None
        grid_distance_km = _great_circle_distance_km(
            float(latitude),
            float(longitude),
            selected_latitude,
            selected_longitude,
        )
        if grid_distance_km > self.nearest_distance_warning_km:
            warnings.warn(
                (
                    f"Requested ERA5 site ({latitude:.6f}, {longitude:.6f}) is "
                    f"{grid_distance_km:.2f} km from selected grid point "
                    f"({selected_latitude:.6f}, {selected_longitude:.6f}); "
                    "results represent the ERA5 grid cell."
                ),
                UserWarning,
                stacklevel=2,
            )

        annual_dataset.attrs.update(
            {
                "dataset": "ERA5 Single Levels",
                "resource_year": self.resource_year,
                "requested_latitude": float(latitude),
                "requested_longitude": float(longitude),
                "selected_latitude": selected_latitude,
                "selected_longitude": selected_longitude,
                "grid_distance_km": grid_distance_km,
                "spatial_method": "nearest",
                "nearest_distance_warning_km": self.nearest_distance_warning_km,
                "data_timezone": "UTC",
                "time_step_seconds": 3600,
                "categories": requested_categories,
                "source_files": tuple(source_files),
                "expver_values": tuple(sorted(expver_values)),
                "number": deterministic_number,
            }
        )
        return annual_dataset

    def _validate_monthly_dataset(
        self, dataset: Any, category: str, filepath: Path
    ) -> None:
        """Validate structure, variables, units, and deterministic coordinates."""

        required_coordinates = {
            ERA5_TIME_DIMENSION,
            *ERA5_SPATIAL_DIMENSIONS,
            "expver",
            "number",
        }
        missing_coordinates = required_coordinates.difference(dataset.coords)
        if missing_coordinates:
            raise ValueError(
                f"{filepath.name} is missing ERA5 coordinates: "
                f"{', '.join(sorted(missing_coordinates))}."
            )

        missing_variables = ERA5_REQUIRED_VARIABLES[category].difference(dataset.data_vars)
        if missing_variables:
            raise ValueError(
                f"{filepath.name} is missing required {category} variables: "
                f"{', '.join(sorted(missing_variables))}."
            )

        for variable_name in ERA5_REQUIRED_VARIABLES[category]:
            variable = dataset[variable_name]
            expected_dimensions = (ERA5_TIME_DIMENSION, *ERA5_SPATIAL_DIMENSIONS)
            if variable.dims != expected_dimensions:
                raise ValueError(
                    f"{filepath.name}:{variable_name} dimensions are {variable.dims}; "
                    f"expected {expected_dimensions}."
                )
            units = variable.attrs.get("units")
            if units not in ERA5_EXPECTED_UNITS[variable_name]:
                raise ValueError(
                    f"{filepath.name}:{variable_name} has units {units!r}; "
                    f"expected one of {sorted(ERA5_EXPECTED_UNITS[variable_name])}."
                )

        number = dataset["number"]
        if number.size != 1:
            raise ValueError(
                f"{filepath.name} contains {number.size} ensemble members; "
                "only one deterministic member is supported."
            )

        expver_values = np.unique(dataset["expver"].values)
        if expver_values.size != 1:
            raise ValueError(
                f"{filepath.name} contains multiple expver values: "
                f"{expver_values.tolist()}."
            )

        for coordinate_name in ERA5_SPATIAL_DIMENSIONS:
            coordinate_values = np.asarray(dataset[coordinate_name].values)
            if coordinate_values.ndim != 1 or coordinate_values.size == 0:
                raise ValueError(
                    f"{filepath.name}:{coordinate_name} must be a non-empty 1D coordinate."
                )
            if not np.all(np.isfinite(coordinate_values)):
                raise ValueError(
                    f"{filepath.name}:{coordinate_name} contains non-finite values."
                )
            coordinate_differences = np.diff(coordinate_values)
            if coordinate_differences.size and not (
                np.all(coordinate_differences > 0.0)
                or np.all(coordinate_differences < 0.0)
            ):
                raise ValueError(
                    f"{filepath.name}:{coordinate_name} must be strictly monotonic."
                )

    @staticmethod
    def _validate_consistent_grid(
        dataset: Any,
        reference_grid: dict[str, np.ndarray] | None,
        filepath: Path,
    ) -> dict[str, np.ndarray]:
        """Validate that all monthly and category grids are identical."""

        current_grid = {
            coordinate_name: np.asarray(dataset[coordinate_name].values)
            for coordinate_name in ERA5_SPATIAL_DIMENSIONS
        }
        if reference_grid is None:
            return current_grid
        for coordinate_name, coordinate_values in current_grid.items():
            if not np.array_equal(coordinate_values, reference_grid[coordinate_name]):
                raise ValueError(
                    f"{filepath.name}:{coordinate_name} is inconsistent with the ERA5 grid."
                )
        return reference_grid

    @staticmethod
    def _validate_selected_data(
        dataset: Any, category: str, filepath: Path
    ) -> None:
        """Validate finite values after selecting the requested grid point."""

        for variable_name in ERA5_REQUIRED_VARIABLES[category]:
            if not np.all(np.isfinite(dataset[variable_name].values)):
                raise ValueError(
                    f"{filepath.name}:{variable_name} contains missing or non-finite values "
                    "at the selected ERA5 grid point."
                )

    @staticmethod
    def _validate_requested_location(
        dataset: Any,
        latitude: float,
        normalized_longitude: float,
    ) -> None:
        """Reject requested coordinates outside the ERA5 grid domain."""

        latitude_values = np.asarray(dataset["latitude"].values)
        longitude_values = np.asarray(dataset["longitude"].values)
        latitude_bounds = (float(latitude_values.min()), float(latitude_values.max()))
        longitude_bounds = (float(longitude_values.min()), float(longitude_values.max()))
        if not latitude_bounds[0] <= latitude <= latitude_bounds[1]:
            raise ValueError(
                f"Requested latitude {latitude} is outside ERA5 domain {latitude_bounds}."
            )
        if not longitude_bounds[0] <= normalized_longitude <= longitude_bounds[1]:
            raise ValueError(
                f"Requested longitude {normalized_longitude} is outside "
                f"ERA5 domain {longitude_bounds}."
            )

    def _validate_annual_time(
        self, dataset: Any, n_timesteps: int | None
    ) -> Any:
        """Validate annual hourly continuity and optionally remove February 29."""

        valid_time = pd.DatetimeIndex(dataset[ERA5_TIME_DIMENSION].values)
        if not valid_time.is_monotonic_increasing:
            raise ValueError("ERA5 valid_time must be strictly increasing.")
        if valid_time.has_duplicates:
            raise ValueError("ERA5 valid_time contains duplicate timestamps.")
        if len(valid_time) > 1:
            time_differences = np.diff(valid_time.asi8)
            expected_difference_nanoseconds = pd.Timedelta(hours=1).value
            if not np.all(time_differences == expected_difference_nanoseconds):
                raise ValueError("ERA5 valid_time must be continuous at hourly resolution.")

        if not np.all(valid_time.year == self.resource_year):
            years = sorted(set(valid_time.year.tolist()))
            raise ValueError(
                f"ERA5 valid_time contains years {years}; expected only {self.resource_year}."
            )

        if not self.include_leap_day:
            retain_time = ~((valid_time.month == 2) & (valid_time.day == 29))
            dataset = dataset.isel({ERA5_TIME_DIMENSION: retain_time})
            valid_time = valid_time[retain_time]

        default_n_timesteps = (
            8784 if self.include_leap_day and calendar.isleap(self.resource_year) else 8760
        )
        expected_n_timesteps = default_n_timesteps if n_timesteps is None else int(n_timesteps)
        if len(valid_time) != expected_n_timesteps:
            raise ValueError(
                f"ERA5 annual series has {len(valid_time)} timesteps; "
                f"expected {expected_n_timesteps}."
            )
        return dataset
