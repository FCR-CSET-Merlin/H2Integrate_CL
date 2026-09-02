"""OpenMDAO resource component for local Sup3rWind CSV files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from attrs import define, field

from h2integrate.resource.resource_base import ResourceBaseAPIConfig
from h2integrate.resource.utilities.file_tools import check_resource_dir
from h2integrate.resource.wind.wind_resource_base import WindResourceBaseAPIModel


TIME_COLUMNS = ("Year", "Month", "Day", "Hour", "Minute")
COMPACT_COLUMN_PATTERN = re.compile(
    r"^(?P<variable>windspeed|winddirection|pressure|temperature|relativehumidity)"
    r"_(?P<height>\d+)m$"
)


@define(kw_only=True)
class Sup3rWindResourceConfig(ResourceBaseAPIConfig):
    """Configuration for a local, hourly Sup3rWind CSV resource."""

    resource_year: int = field(converter=int)
    resource_dir: Path | str | None = field(default=None)
    resource_filename: Path | str = field(default="")
    include_leap_day: bool = field(default=False, converter=bool)
    resource_data: dict | object = field(factory=dict)
    dataset_desc: str = field(default="sup3rwind", init=False)
    resource_type: str = field(default="wind", init=False)


class Sup3rWindResource(WindResourceBaseAPIModel):
    """Read a local Sup3rWind CSV into H2Integrate's wind resource contract.

    Supports Wind Toolkit-style files and compact Chilean extractions with
    ``# key=value`` metadata. Data and simulation time must be hourly UTC.
    """

    def setup(self) -> None:
        resource_specs = self.helper_setup_method()
        self.config = Sup3rWindResourceConfig.from_dict(
            resource_specs, additional_cls_name=self.__class__.__name__
        )
        super().setup()
        self._validate_simulation_contract()
        if not self.config.resource_filename:
            raise ValueError(
                "Sup3rWindResource requires resource_filename in resource_parameters."
            )
        self.resource_data = self.get_data(self.config.latitude, self.config.longitude)
        self.add_discrete_output(
            "wind_resource_data",
            val=self.resource_data,
            desc="Dict of local Sup3rWind resource data",
        )

    def create_filename(self, latitude: float, longitude: float) -> str:
        """Return the required user-provided filename."""
        del latitude, longitude
        return str(self.config.resource_filename)

    def get_data(
        self, latitude: float, longitude: float, first_call: bool = True
    ) -> dict[str, Any]:
        """Load only an explicitly configured local file without API fallback."""
        del latitude, longitude, first_call
        if bool(self.config.resource_data):
            return self.add_resource_start_end_times(self.config.resource_data)

        resource_dir = check_resource_dir(resource_dir=self.config.resource_dir)
        filename = Path(self.config.resource_filename)
        candidates = (resource_dir / filename, resource_dir / "wind" / filename)
        filepath = next((candidate for candidate in candidates if candidate.is_file()), None)
        if filepath is None:
            searched = ", ".join(str(candidate) for candidate in candidates)
            raise FileNotFoundError(
                "Sup3rWind resource file was not found. This local-only component does not "
                f"download Sup3rWind data. Searched: {searched}."
            )
        self.filepath = filepath
        data = self.load_data(filepath)
        return self.add_resource_start_end_times(data)

    def create_url(self, latitude: float, longitude: float) -> str:
        """Reject implicit downloads because this is a local-file adapter."""
        del latitude, longitude
        raise FileNotFoundError(
            "Sup3rWind resource file was not found. Supply an existing resource_dir and "
            "resource_filename; this component does not download Sup3rWind data."
        )

    def load_data(self, fpath: str | Path) -> dict[str, Any]:
        """Load and validate a compact or Wind Toolkit-style Sup3rWind CSV."""
        filepath = Path(fpath)
        with filepath.open(encoding="utf-8-sig") as stream:
            first_line = stream.readline()
        if first_line.startswith("#"):
            data = self._load_compact_csv(filepath)
        elif first_line.startswith("SiteID,"):
            data = self._load_wtk_csv(filepath)
        else:
            raise ValueError(
                f"Unsupported Sup3rWind CSV layout in {filepath}. Expected a '#'-metadata "
                "or 'SiteID,' first line."
            )
        return self._process_and_validate_time(data, filepath)

    def _load_compact_csv(self, filepath: Path) -> dict[str, Any]:
        metadata: dict[str, str] = {}
        with filepath.open(encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.startswith("#"):
                    break
                key, separator, value = line[1:].strip().partition("=")
                if separator:
                    metadata[key.strip()] = value.strip()
        frame = pd.read_csv(filepath, comment="#")
        if "timestamp" not in frame:
            raise ValueError(f"Compact Sup3rWind file {filepath} has no timestamp column.")
        timestamps = pd.to_datetime(frame.pop("timestamp"), errors="raise")
        data = self._standardize_compact_columns(frame)
        data.update(self._time_arrays(timestamps))
        data.update(
            {
                "site_id": metadata.get("grid_gid", ""),
                "site_tz": 0.0,
                "data_tz": 0.0,
                "site_lat": float(metadata.get("grid_latitude", self.config.latitude)),
                "site_lon": float(metadata.get("grid_longitude", self.config.longitude)),
                "requested_latitude": float(
                    metadata.get("requested_latitude", self.config.latitude)
                ),
                "requested_longitude": float(
                    metadata.get("requested_longitude", self.config.longitude)
                ),
                "filepath": str(filepath),
                "dataset": metadata.get("product", "Sup3rWind"),
            }
        )
        if "grid_distance_km" in metadata:
            data["grid_distance_km"] = float(metadata["grid_distance_km"])
        return data

    def _standardize_compact_columns(self, frame: pd.DataFrame) -> dict[str, np.ndarray]:
        variable_names = {
            "windspeed": "wind_speed",
            "winddirection": "wind_direction",
            "pressure": "pressure",
            "temperature": "temperature",
            "relativehumidity": "relative_humidity",
        }
        data: dict[str, np.ndarray] = {}
        for column in frame.columns:
            match = COMPACT_COLUMN_PATTERN.match(column)
            if match is None:
                continue
            output_name = f"{variable_names[match['variable']]}_{match['height']}m"
            values = frame[column].astype(float).to_numpy()
            if match["variable"] == "pressure":
                values = values / 101_325.0
            data[output_name] = values
        if not any(name.startswith("wind_speed_") for name in data):
            raise ValueError("Sup3rWind compact CSV contains no height-specific wind speed.")
        return data

    def _load_wtk_csv(self, filepath: Path) -> dict[str, Any]:
        frame = pd.read_csv(filepath, header=1).dropna(axis=1, how="all")
        header = pd.read_csv(filepath, nrows=1, header=None).values[0]
        metadata = dict(zip(header[0::2], header[1::2]))
        frame_data, data_units = self.format_timeseries_data(frame)
        data, _ = self.compare_units_and_correct(frame_data, data_units)
        data.update(
            {
                "site_id": metadata["SiteID"],
                "site_tz": float(metadata["Site Timezone"]),
                "data_tz": float(metadata["Data Timezone"]),
                "site_lat": float(metadata["Latitude"]),
                "site_lon": float(metadata["Longitude"]),
                "filepath": str(filepath),
                "dataset": "Sup3rWind",
            }
        )
        return data

    def format_timeseries_data(
        self, frame: pd.DataFrame
    ) -> tuple[dict[str, np.ndarray], dict[str, str]]:
        """Normalize Wind Toolkit-style column names and units."""
        data: dict[str, np.ndarray] = {}
        data_units: dict[str, str] = {}
        for column in frame.columns:
            if column in TIME_COLUMNS:
                data[column.lower()] = frame[column].astype(float).to_numpy()
                continue
            units = column.rsplit("(", 1)[-1].rstrip(")")
            name = column.rsplit("(", 1)[0].strip().lower()
            name = name.replace("surface air pressure", "pressure at 0m")
            name = name.replace("air temperature", "temperature")
            name = name.replace("wind speed", "wind_speed")
            name = name.replace("wind direction", "wind_direction")
            name = name.replace("relative humidity", "relative_humidity")
            name = name.replace(" at ", "_").replace(" ", "_")
            normalized_units = units.replace("%", "percent").replace("degrees", "deg")
            if normalized_units == "C":
                normalized_units = "degC"
            data[name] = frame[column].astype(float).to_numpy()
            data_units[name] = normalized_units
        return data, data_units

    def _process_and_validate_time(
        self, data: dict[str, Any], filepath: Path
    ) -> dict[str, Any]:
        time_keys = ("year", "month", "day", "hour", "minute")
        timestamps = pd.to_datetime(
            {key: np.asarray(data[key], dtype=int) for key in time_keys}
        )
        if not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
            raise ValueError(f"Sup3rWind timestamps in {filepath} must be unique and increasing.")
        hourly_nanoseconds = 3_600_000_000_000
        timestamp_nanoseconds = timestamps.astype("int64").to_numpy()
        if len(timestamps) > 1 and not np.all(
            np.diff(timestamp_nanoseconds) == hourly_nanoseconds
        ):
            raise ValueError(f"Sup3rWind timestamps in {filepath} must have an hourly cadence.")
        if not np.all(timestamps.dt.year == self.config.resource_year):
            raise ValueError(
                f"Sup3rWind data year does not match resource_year={self.config.resource_year}."
            )
        if not np.isclose(float(data["data_tz"]), 0.0):
            raise ValueError("Sup3rWindResource requires CSV timestamps in UTC (data_tz=0).")
        leap_day = (timestamps.dt.month == 2) & (timestamps.dt.day == 29)
        keep = np.arange(len(timestamps))
        if not self.config.include_leap_day:
            keep = keep[~leap_day.to_numpy()]
        if len(keep) != self.n_timesteps:
            raise ValueError(
                f"Sup3rWindResource: resource data has {len(keep)} timesteps after leap-day "
                f"processing; plant simulation requires {self.n_timesteps}."
            )
        original_length = len(timestamps)
        for key, value in list(data.items()):
            if isinstance(value, np.ndarray) and len(value) == original_length:
                data[key] = value[keep]
        return data

    @staticmethod
    def _time_arrays(timestamps: pd.Series) -> dict[str, np.ndarray]:
        return {
            "year": timestamps.dt.year.to_numpy(dtype=float),
            "month": timestamps.dt.month.to_numpy(dtype=float),
            "day": timestamps.dt.day.to_numpy(dtype=float),
            "hour": timestamps.dt.hour.to_numpy(dtype=float),
            "minute": timestamps.dt.minute.to_numpy(dtype=float),
        }

    def _validate_simulation_contract(self) -> None:
        if not np.isclose(float(self.dt), 3600.0):
            raise ValueError("Sup3rWindResource requires plant simulation dt=3600 seconds.")
        if not np.isclose(float(self.config.timezone), 0.0):
            raise ValueError("Sup3rWindResource requires plant simulation timezone=0 (UTC).")
