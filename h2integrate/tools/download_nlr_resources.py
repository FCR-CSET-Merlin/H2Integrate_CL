"""Download point-based Sup3rWind and NSRDB resources from the NLR API.

The downloader deliberately stores the response body without transforming it and writes a
sidecar JSON document containing the non-sensitive request parameters and a SHA-256 checksum.
All requests are sequential and use hourly UTC data so the resulting files can be reviewed and
published separately from the source repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterable

import requests

from h2integrate.resource.utilities.nlr_developer_api_keys import (
    get_nlr_developer_api_email,
    get_nlr_developer_api_key,
)


SUP3RWIND_ENDPOINT: Final = (
    "https://developer.nlr.gov/api/wind-toolkit/v2/wind/"
    "wtk-sup3rwind-south-america-v1-0-0-60min-download.csv"
)
NSRDB_ENDPOINT: Final = (
    "https://developer.nlr.gov/api/nsrdb/v2/solar/"
    "nsrdb-GOES-full-disc-v4-0-0-download.csv"
)

WIND_YEARS: Final = range(2005, 2025)
SOLAR_YEARS: Final = range(2018, 2026)
AVAILABLE_WIND_HEIGHTS_M: Final = (10, 40, 80, 100, 120, 160, 200)
DEFAULT_WIND_HEIGHTS_M: Final = (100, 120)
DEFAULT_OUTPUT_DIR: Final = Path("data/raw")
DEFAULT_REQUEST_DELAY_SECONDS: Final = 1.1
DEFAULT_TIMEOUT_SECONDS: Final = 120.0

WIND_AUXILIARY_ATTRIBUTES: Final = (
    "pressure_0m",
    "relativehumidity_2m",
    "temperature_2m",
)
SOLAR_ATTRIBUTES: Final = (
    "air_temperature",
    "dhi",
    "dni",
    "ghi",
    "relative_humidity",
    "solar_zenith_angle",
    "surface_albedo",
    "surface_pressure",
    "wind_direction",
    "wind_speed",
)

_SITE_NAME_PATTERN: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_SENSITIVE_PARAMETER_NAMES: Final = {"api_key", "email"}


class NLRDownloadError(RuntimeError):
    """Raised when an NLR response cannot be safely stored as a resource CSV."""


@dataclass(frozen=True)
class DownloadTask:
    """Description of one point, resource, and year to download."""

    resource: str
    site: str
    latitude: float
    longitude: float
    year: int
    wind_heights_m: tuple[int, ...] = DEFAULT_WIND_HEIGHTS_M


@dataclass(frozen=True)
class DownloadResult:
    """Files and status produced by one download attempt."""

    csv_path: Path
    metadata_path: Path
    downloaded: bool


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate latitude and longitude in decimal degrees."""
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"Latitude must be between -90 and 90 degrees; received {latitude}.")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"Longitude must be between -180 and 180 degrees; received {longitude}.")


def make_wkt(latitude: float, longitude: float) -> str:
    """Return an API-compatible WKT point from decimal-degree coordinates."""
    validate_coordinates(latitude, longitude)
    return f"POINT({longitude} {latitude})"


def validate_site_name(site: str) -> str:
    """Validate a site identifier before it is used in local paths."""
    if not _SITE_NAME_PATTERN.fullmatch(site):
        raise ValueError(
            "Site identifiers must start with an alphanumeric character and contain only "
            "letters, numbers, underscores, or hyphens."
        )
    return site


def validate_wind_heights(heights_m: Iterable[int]) -> tuple[int, ...]:
    """Validate and normalize requested Sup3rWind heights in metres."""
    normalized = tuple(dict.fromkeys(heights_m))
    if not normalized:
        raise ValueError("At least one Sup3rWind height is required.")
    unsupported = sorted(set(normalized).difference(AVAILABLE_WIND_HEIGHTS_M))
    if unsupported:
        raise ValueError(
            f"Unsupported Sup3rWind heights {unsupported}; available heights are "
            f"{list(AVAILABLE_WIND_HEIGHTS_M)} m."
        )
    return normalized


def validate_year(resource: str, year: int) -> None:
    """Validate a year against the documented availability of one NLR dataset."""
    valid_years = WIND_YEARS if resource == "sup3rwind" else SOLAR_YEARS
    if resource not in {"sup3rwind", "nsrdb"}:
        raise ValueError(f"Unsupported resource {resource!r}.")
    if year not in valid_years:
        raise ValueError(
            f"Year {year} is unavailable for {resource}; supported years are "
            f"{valid_years.start}-{valid_years.stop - 1}."
        )


def wind_attributes(heights_m: Iterable[int]) -> tuple[str, ...]:
    """Return Sup3rWind attributes for auxiliary data and requested heights."""
    heights = validate_wind_heights(heights_m)
    attributes = list(WIND_AUXILIARY_ATTRIBUTES)
    for height_m in heights:
        attributes.extend((f"windspeed_{height_m}m", f"winddirection_{height_m}m"))
    return tuple(attributes)


def build_download_tasks(
    *,
    site: str,
    latitude: float,
    longitude: float,
    years: Iterable[int],
    resource: str,
    wind_heights_m: Iterable[int] = DEFAULT_WIND_HEIGHTS_M,
) -> tuple[list[DownloadTask], list[str]]:
    """Build valid sequential tasks and warnings for resource/year mismatches."""
    validate_site_name(site)
    validate_coordinates(latitude, longitude)
    heights = validate_wind_heights(wind_heights_m)
    requested_years = tuple(dict.fromkeys(years))
    if not requested_years:
        raise ValueError("At least one year is required.")
    if resource not in {"wind", "solar", "both"}:
        raise ValueError("Resource must be one of: wind, solar, both.")

    resource_names = {
        "wind": ("sup3rwind",),
        "solar": ("nsrdb",),
        "both": ("sup3rwind", "nsrdb"),
    }[resource]
    tasks: list[DownloadTask] = []
    warnings: list[str] = []
    for year in requested_years:
        for resource_name in resource_names:
            try:
                validate_year(resource_name, year)
            except ValueError as error:
                if resource == "both":
                    warnings.append(f"Skipping {resource_name} for {year}: {error}")
                    continue
                raise
            tasks.append(
                DownloadTask(
                    resource=resource_name,
                    site=site,
                    latitude=latitude,
                    longitude=longitude,
                    year=year,
                    wind_heights_m=heights,
                )
            )
    if not tasks:
        raise ValueError("None of the requested resource/year combinations is available.")
    return tasks, warnings


def get_credentials() -> tuple[str, str]:
    """Load the NLR API key and email using the repository credential convention."""
    try:
        return get_nlr_developer_api_key(), get_nlr_developer_api_email()
    except ValueError as error:
        raise ValueError(
            "NLR credentials are required. Set NLR_API_KEY and NLR_API_EMAIL; do not add "
            "them to command history, source files, or metadata."
        ) from error


def request_parameters(task: DownloadTask, api_key: str, email: str) -> dict[str, str]:
    """Construct documented NLR query parameters for one task."""
    common = {
        "api_key": api_key,
        "wkt": make_wkt(task.latitude, task.longitude),
        "names": str(task.year),
        "utc": "true",
        "leap_day": "false",
        "interval": "60",
        "email": email,
    }
    if task.resource == "sup3rwind":
        attributes = wind_attributes(task.wind_heights_m)
    elif task.resource == "nsrdb":
        attributes = SOLAR_ATTRIBUTES
    else:
        raise ValueError(f"Unsupported resource {task.resource!r}.")
    return {**common, "attributes": ",".join(attributes)}


def output_paths(task: DownloadTask, output_dir: Path) -> tuple[Path, Path]:
    """Return deterministic raw CSV and request-metadata paths for one task."""
    resource_dir = output_dir / task.resource / task.site / str(task.year)
    if task.resource == "sup3rwind":
        stem = f"{task.site}_sup3rwind_{task.year}"
    else:
        stem = f"{task.site}_nsrdb_goes_full_disc_v4_{task.year}"
    return resource_dir / f"{stem}.csv", resource_dir / f"{stem}.request.json"


def _looks_like_resource_csv(content: bytes) -> bool:
    """Return whether a response resembles an NLR resource CSV rather than an error page."""
    if not content:
        return False
    preview = content[:16384].decode("utf-8-sig", errors="replace").lstrip()
    if preview.startswith(("<", "{", "[")) or "," not in preview:
        return False
    normalized = preview.lower().replace(" ", "")
    metadata_markers = ("siteid,", "locationid,", "latitude,longitude")
    time_markers = ("year,month,day,hour,minute", "year,month,day,hour")
    return any(marker in normalized for marker in metadata_markers + time_markers)


def _write_temporary(path: Path, content: bytes) -> Path:
    """Write bytes to a sibling temporary file and return its path."""
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.part")
    with temporary_path.open("wb") as temporary_file:
        temporary_file.write(content)
        temporary_file.flush()
        os.fsync(temporary_file.fileno())
    return temporary_path


def _safe_request_parameters(parameters: dict[str, str]) -> dict[str, str]:
    """Remove credentials from request parameters before persistence."""
    return {
        name: value
        for name, value in parameters.items()
        if name.lower() not in _SENSITIVE_PARAMETER_NAMES
    }


def _task_context(task: DownloadTask) -> str:
    """Return non-sensitive context for operational messages."""
    return (
        f"{task.resource}/{task.site}/{task.year} "
        f"at ({task.latitude}, {task.longitude})"
    )


def download_task(
    task: DownloadTask,
    *,
    api_key: str,
    email: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    overwrite: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    session: requests.Session | None = None,
    include_leap_day: bool = False,
) -> DownloadResult:
    """Download one resource CSV and atomically persist it with request metadata."""
    validate_site_name(task.site)
    validate_coordinates(task.latitude, task.longitude)
    validate_year(task.resource, task.year)
    parameters = request_parameters(task, api_key, email)
    parameters["leap_day"] = str(include_leap_day).lower()
    endpoint = SUP3RWIND_ENDPOINT if task.resource == "sup3rwind" else NSRDB_ENDPOINT
    csv_path, metadata_path = output_paths(task, Path(output_dir))

    existing_paths = [path for path in (csv_path, metadata_path) if path.exists()]
    if len(existing_paths) == 2 and not overwrite:
        return DownloadResult(csv_path=csv_path, metadata_path=metadata_path, downloaded=False)
    if existing_paths and not overwrite:
        raise FileExistsError(
            "A partial prior result exists. Inspect it and use --overwrite to replace both "
            f"files: {', '.join(str(path) for path in existing_paths)}"
        )

    request_session = session or requests.Session()
    try:
        response = request_session.get(endpoint, params=parameters, timeout=timeout_seconds)
    except requests.Timeout as error:
        raise NLRDownloadError(
            f"NLR request timed out for {_task_context(task)}."
        ) from error
    except requests.RequestException as error:
        raise NLRDownloadError(
            f"NLR request failed for {_task_context(task)}: "
            f"{error.__class__.__name__}."
        ) from error

    if not 200 <= response.status_code < 300:
        raise NLRDownloadError(
            f"NLR returned HTTP {response.status_code} for {_task_context(task)}."
        )
    content = response.content
    if not _looks_like_resource_csv(content):
        raise NLRDownloadError(
            f"NLR returned HTTP {response.status_code}, but the body is not a recognizable "
            f"resource CSV for {_task_context(task)}."
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    downloaded_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "dataset": (
            "sup3rwind-south-america-v1-0-0-60min"
            if task.resource == "sup3rwind"
            else "nsrdb-GOES-full-disc-v4-0-0"
        ),
        "resource": task.resource,
        "site": task.site,
        "latitude": task.latitude,
        "longitude": task.longitude,
        "year": task.year,
        "temporal_resolution_minutes": 60,
        "timezone": "UTC",
        "request": {
            "endpoint": endpoint,
            "parameters": _safe_request_parameters(parameters),
        },
        "response": {
            "downloaded_at_utc": downloaded_at,
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    }
    metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")

    csv_temporary_path: Path | None = None
    metadata_temporary_path: Path | None = None
    try:
        csv_temporary_path = _write_temporary(csv_path, content)
        metadata_temporary_path = _write_temporary(metadata_path, metadata_bytes)
        os.replace(metadata_temporary_path, metadata_path)
        metadata_temporary_path = None
        os.replace(csv_temporary_path, csv_path)
        csv_temporary_path = None
    finally:
        for temporary_path in (csv_temporary_path, metadata_temporary_path):
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    return DownloadResult(csv_path=csv_path, metadata_path=metadata_path, downloaded=True)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the NLR resource downloader."""
    parser = argparse.ArgumentParser(
        description="Download raw hourly UTC Sup3rWind and/or NSRDB point resources."
    )
    parser.add_argument("--site", required=True, help="Safe identifier used in output paths.")
    parser.add_argument(
        "--lat",
        "--latitude",
        dest="latitude",
        required=True,
        type=float,
        help="Latitude in decimal degrees.",
    )
    parser.add_argument(
        "--lon",
        "--longitude",
        dest="longitude",
        required=True,
        type=float,
        help="Longitude in decimal degrees.",
    )
    parser.add_argument("--years", required=True, type=int, nargs="+", help="One or more years.")
    parser.add_argument(
        "--resource",
        choices=("wind", "solar", "both"),
        default="both",
        help="Resource family to download (default: both).",
    )
    parser.add_argument(
        "--wind-heights",
        type=int,
        nargs="+",
        default=DEFAULT_WIND_HEIGHTS_M,
        metavar="METRES",
        help="Sup3rWind heights (default: 100 120).",
    )
    parser.add_argument(
        "--output",
        "--output-dir",
        dest="output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Root for ignored raw files (default: data/raw).",
    )
    parser.add_argument(
        "--include-leap-day",
        action="store_true",
        help="Request 29 February when applicable (default: excluded).",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing file pair.")
    parser.add_argument(
        "--request-delay",
        type=float,
        default=DEFAULT_REQUEST_DELAY_SECONDS,
        help="Seconds between sequential API requests (default: 1.1).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-request timeout in seconds (default: 120).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run sequential downloads requested on the command line."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.request_delay < 0:
        parser.error("--request-delay cannot be negative.")
    if arguments.timeout <= 0:
        parser.error("--timeout must be positive.")
    try:
        tasks, warnings = build_download_tasks(
            site=arguments.site,
            latitude=arguments.latitude,
            longitude=arguments.longitude,
            years=arguments.years,
            resource=arguments.resource,
            wind_heights_m=arguments.wind_heights,
        )
        api_key, email = get_credentials()
    except ValueError as error:
        parser.error(str(error))

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    session = requests.Session()
    for task_index, task in enumerate(tasks):
        try:
            result = download_task(
                task,
                api_key=api_key,
                email=email,
                output_dir=arguments.output_dir,
                overwrite=arguments.overwrite,
                timeout_seconds=arguments.timeout,
                session=session,
                include_leap_day=arguments.include_leap_day,
            )
        except (NLRDownloadError, FileExistsError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        action = "downloaded" if result.downloaded else "already present"
        size_suffix = f" ({result.csv_path.stat().st_size} bytes)" if result.downloaded else ""
        print(f"{action}: {result.csv_path}{size_suffix}")
        print(f"metadata: {result.metadata_path}")
        if result.downloaded and task_index < len(tasks) - 1:
            time.sleep(arguments.request_delay)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
