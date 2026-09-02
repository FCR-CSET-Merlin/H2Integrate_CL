"""OpenMDAO resource components for local ERA5 Single Levels data."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from attrs import field, define

from h2integrate.core.validators import gte_zero, range_val
from h2integrate.resource.era5_reader import ERA5SingleLevelsReader
from h2integrate.resource.era5_solar import (
    DEFAULT_MAXIMUM_ZENITH_ANGLE_DEG,
    transform_era5_solar_dataset,
)
from h2integrate.resource.era5_wind import transform_era5_wind_dataset
from h2integrate.resource.resource_base import ResourceBaseAPIConfig, ResourceBaseAPIModel


@define(kw_only=True)
class ERA5SingleLevelsResourceConfig(ResourceBaseAPIConfig):
    """Shared configuration for local ERA5 Single Levels resources.

    Args:
        resource_year: Calendar year identified by the ERA5 ``valid_time`` values.
        resource_dir: Directory containing monthly NetCDF files.
        file_patterns: Optional category-to-pattern overrides for monthly filenames.
        nearest_distance_warning_km: Configurable distance above which nearest-point
            selection emits a warning. Defaults to 15 km.
        include_leap_day: Whether February 29 is retained for leap years.
        site_elevation_m: Optional configured site elevation in m. It takes
            precedence over elevation derived from ERA5 geopotential.
    """

    resource_year: int = field(converter=int)
    resource_dir: Path | str | None = field(default=None)
    file_patterns: Mapping[str, str] = field(factory=dict, converter=dict)
    nearest_distance_warning_km: float = field(
        default=15.0,
        converter=float,
        validator=gte_zero,
    )
    include_leap_day: bool = field(default=False, converter=bool)
    site_elevation_m: float | None = field(default=None)
    dataset_desc: str = field(default="era5_single_levels", init=False)


@define(kw_only=True)
class ERA5SingleLevelsWindResourceConfig(ERA5SingleLevelsResourceConfig):
    """Configuration for :class:`ERA5SingleLevelsWindResource`."""

    resource_type: str = field(default="wind", init=False)


@define(kw_only=True)
class ERA5SingleLevelsSolarResourceConfig(ERA5SingleLevelsResourceConfig):
    """Configuration for :class:`ERA5SingleLevelsSolarResource`."""

    maximum_zenith_angle_deg: float = field(
        default=DEFAULT_MAXIMUM_ZENITH_ANGLE_DEG,
        converter=float,
        validator=range_val(0.000001, 89.999999),
    )
    resource_type: str = field(default="solar", init=False)


class ERA5SingleLevelsResourceBase(ResourceBaseAPIModel):
    """Shared OpenMDAO lifecycle for local ERA5 resource components.

    Subclasses specify the categories to read, the discrete output name, and the
    transformation that maps an annual point dataset to H2Integrate's existing
    wind or solar resource contract.
    """

    config_class: type[ERA5SingleLevelsResourceConfig]
    resource_categories: tuple[str, ...]
    resource_output_name: str

    def setup(self) -> None:
        """Configure the reader and expose the transformed resource dictionary."""

        resource_specs = self._prepare_resource_specs()
        self.config = self.config_class.from_dict(
            resource_specs,
            additional_cls_name=self.__class__.__name__,
        )
        super().setup()
        self._validate_simulation_contract()

        if self.config.resource_dir is None:
            raise ValueError(
                f"{self.__class__.__name__} requires resource_dir in resource_parameters."
            )
        self.reader = ERA5SingleLevelsReader(
            resource_dir=self.config.resource_dir,
            resource_year=self.config.resource_year,
            file_patterns=self.config.file_patterns,
            nearest_distance_warning_km=self.config.nearest_distance_warning_km,
            include_leap_day=self.config.include_leap_day,
        )
        self.resource_data = self._load_resource_data(
            self.config.latitude,
            self.config.longitude,
        )
        self.add_discrete_output(
            self.resource_output_name,
            val=self.resource_data,
            desc=f"ERA5 Single Levels {self.config.resource_type} resource data dictionary",
        )

    def compute(
        self,
        inputs: Any,
        outputs: Any,
        discrete_inputs: Any,
        discrete_outputs: Any,
    ) -> None:
        """Reload the selected point only when variable site coordinates change."""

        if self.config.use_fixed_resource_location:
            return
        latitude = float(inputs["latitude"][0])
        longitude = float(inputs["longitude"][0])
        if np.allclose(
            [latitude, longitude],
            self.resource_site,
            atol=1.0e-6,
            rtol=0.0,
        ):
            return

        self.resource_data = self._load_resource_data(latitude, longitude)
        self.resource_site = [latitude, longitude]
        discrete_outputs[self.resource_output_name] = self.resource_data

    def _prepare_resource_specs(self) -> dict[str, Any]:
        """Merge resource parameters with site and simulation defaults."""

        resource_specs = dict(self.options["resource_config"])
        site_config = self.options["plant_config"]["site"]
        simulation_config = self.options["plant_config"]["plant"]["simulation"]
        resource_specs.setdefault("latitude", site_config["latitude"])
        resource_specs.setdefault("longitude", site_config["longitude"])
        resource_specs.setdefault("timezone", simulation_config.get("timezone", 0))
        resource_specs.setdefault("site_elevation_m", site_config.get("elevation"))
        return resource_specs

    def _validate_simulation_contract(self) -> None:
        """Require the hourly simulation contract implemented by ERA5 adapters."""

        if not np.isclose(float(self.dt), 3600.0, rtol=0.0, atol=1.0e-9):
            raise ValueError(
                f"{self.__class__.__name__} requires plant simulation dt=3600 seconds; "
                f"received {self.dt}."
            )
        if not np.isclose(float(self.config.timezone), 0.0, rtol=0.0, atol=1.0e-9):
            raise ValueError(
                f"{self.__class__.__name__} requires plant simulation timezone=0 (UTC); "
                f"received {self.config.timezone}."
            )
        if int(self.n_timesteps) <= 0:
            raise ValueError("plant simulation n_timesteps must be greater than zero.")

    def _load_resource_data(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Read an annual point dataset and apply the subclass transformation."""

        dataset = self.reader.read_site(
            latitude=latitude,
            longitude=longitude,
            categories=self.resource_categories,
            n_timesteps=self.n_timesteps,
        )
        return self.transform_dataset(dataset)

    def transform_dataset(self, dataset: Any) -> dict[str, Any]:
        """Transform an ERA5 annual point dataset into a resource dictionary."""

        raise NotImplementedError


class ERA5SingleLevelsWindResource(ERA5SingleLevelsResourceBase):
    """Read local ERA5 data and output H2Integrate ``wind_resource_data``."""

    config_class = ERA5SingleLevelsWindResourceConfig
    resource_categories = ("wind", "auxiliary")
    resource_output_name = "wind_resource_data"

    def transform_dataset(self, dataset: Any) -> dict[str, Any]:
        """Apply the common ERA5 wind transformation."""

        return transform_era5_wind_dataset(
            dataset,
            site_elevation_m=self.config.site_elevation_m,
        )


class ERA5SingleLevelsSolarResource(ERA5SingleLevelsResourceBase):
    """Read local ERA5 data and output H2Integrate ``solar_resource_data``."""

    config_class = ERA5SingleLevelsSolarResourceConfig
    resource_categories = ("solar", "wind", "auxiliary")
    resource_output_name = "solar_resource_data"

    def transform_dataset(self, dataset: Any) -> dict[str, Any]:
        """Apply the common ERA5 solar transformation."""

        return transform_era5_solar_dataset(
            dataset,
            site_elevation_m=self.config.site_elevation_m,
            maximum_zenith_angle_deg=self.config.maximum_zenith_angle_deg,
        )
