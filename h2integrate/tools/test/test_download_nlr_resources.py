"""Unit tests for the credentialed NLR resource downloader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from h2integrate.tools import download_nlr_resources as downloader

pytestmark = pytest.mark.unit


RESOURCE_CSV = (
    b"SiteID,Latitude,Longitude\n"
    b"123,-22.2812687,-69.5698745\n"
    b"Year,Month,Day,Hour,Minute,GHI\n"
    b"2023,1,1,0,0,0\n"
)


class FakeResponse:
    """Small requests-response substitute used without network access."""

    def __init__(
        self,
        content: bytes = RESOURCE_CSV,
        status_code: int = 200,
        content_type: str = "text/csv",
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}


class FakeSession:
    """Capture HTTP calls and provide predefined responses or exceptions."""

    def __init__(self, outcomes: list[FakeResponse | Exception]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def get(self, url: str, *, params: dict[str, str], timeout: float) -> FakeResponse:
        self.calls.append((url, params, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_task(resource: str = "sup3rwind") -> downloader.DownloadTask:
    """Return a representative Chilean download task."""
    return downloader.DownloadTask(
        resource=resource,
        site="site_01_antofagasta",
        latitude=-22.2812687,
        longitude=-69.5698745,
        year=2023,
    )


def test_make_wkt_uses_longitude_then_latitude() -> None:
    assert downloader.make_wkt(-25.4, -70.48) == "POINT(-70.48 -25.4)"


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(90.1, 0.0), (-90.1, 0.0), (0.0, 180.1), (0.0, -180.1)],
)
def test_validate_coordinates_rejects_out_of_range(
    latitude: float, longitude: float
) -> None:
    with pytest.raises(ValueError, match="between"):
        downloader.validate_coordinates(latitude, longitude)


def test_validate_site_name_blocks_path_traversal() -> None:
    with pytest.raises(ValueError, match="Site identifiers"):
        downloader.validate_site_name("../site")


def test_validate_wind_heights_normalizes_and_rejects_unknown_values() -> None:
    assert downloader.validate_wind_heights([120, 100, 120]) == (120, 100)
    with pytest.raises(ValueError, match="Unsupported Sup3rWind heights"):
        downloader.validate_wind_heights([115])


@pytest.mark.parametrize(
    ("resource", "valid_year", "invalid_year"),
    [("sup3rwind", 2024, 2025), ("nsrdb", 2025, 2026)],
)
def test_validate_year_uses_dataset_availability(
    resource: str, valid_year: int, invalid_year: int
) -> None:
    downloader.validate_year(resource, valid_year)
    with pytest.raises(ValueError, match="unavailable"):
        downloader.validate_year(resource, invalid_year)


def test_build_tasks_skips_only_unavailable_half_of_both_request() -> None:
    tasks, warnings = downloader.build_download_tasks(
        site="test_site",
        latitude=-22.0,
        longitude=-69.0,
        years=[2025],
        resource="both",
    )

    assert [task.resource for task in tasks] == ["nsrdb"]
    assert "Skipping sup3rwind" in warnings[0]


def test_request_parameters_are_hourly_utc_and_resource_specific() -> None:
    wind_parameters = downloader.request_parameters(make_task(), "secret-key", "user@test.cl")
    solar_parameters = downloader.request_parameters(
        make_task(resource="nsrdb"), "secret-key", "user@test.cl"
    )

    assert wind_parameters["wkt"] == "POINT(-69.5698745 -22.2812687)"
    assert wind_parameters["interval"] == "60"
    assert wind_parameters["utc"] == "true"
    assert wind_parameters["leap_day"] == "false"
    assert "windspeed_100m" in wind_parameters["attributes"]
    assert "windspeed_120m" in wind_parameters["attributes"]
    assert "ghi" in solar_parameters["attributes"]
    assert "windspeed_100m" not in solar_parameters["attributes"]
    assert downloader.NSRDB_ENDPOINT.endswith("nsrdb-GOES-full-disc-v4-0-0-download.csv")
    assert "goes_full_disc_v4" in downloader.output_paths(make_task(resource="nsrdb"), Path("data/raw"))[0].name


def test_download_writes_exact_response_and_non_sensitive_metadata(tmp_path: Path) -> None:
    session = FakeSession([FakeResponse()])
    task = make_task()

    result = downloader.download_task(
        task,
        api_key="secret-key",
        email="private@test.cl",
        output_dir=tmp_path,
        session=session,
    )

    assert result.downloaded
    assert result.csv_path.read_bytes() == RESOURCE_CSV
    metadata_text = result.metadata_path.read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert "secret-key" not in metadata_text
    assert "private@test.cl" not in metadata_text
    assert "api_key" not in metadata["request"]["parameters"]
    assert "email" not in metadata["request"]["parameters"]
    assert metadata["timezone"] == "UTC"
    assert metadata["dataset"] == "sup3rwind-south-america-v1-0-0-60min"
    assert metadata["response"]["size_bytes"] == len(RESOURCE_CSV)
    assert len(metadata["response"]["sha256"]) == 64
    assert session.calls[0][0] == downloader.SUP3RWIND_ENDPOINT
    assert session.calls[0][1]["api_key"] == "secret-key"


def test_download_does_not_overwrite_complete_pair_by_default(tmp_path: Path) -> None:
    task = make_task()
    first_session = FakeSession([FakeResponse()])
    downloader.download_task(
        task,
        api_key="secret",
        email="user@test.cl",
        output_dir=tmp_path,
        session=first_session,
    )
    second_session = FakeSession([])

    result = downloader.download_task(
        task,
        api_key="secret",
        email="user@test.cl",
        output_dir=tmp_path,
        session=second_session,
    )

    assert not result.downloaded
    assert second_session.calls == []


def test_download_requires_overwrite_for_partial_prior_result(tmp_path: Path) -> None:
    task = make_task()
    csv_path, _ = downloader.output_paths(task, tmp_path)
    csv_path.parent.mkdir(parents=True)
    csv_path.write_bytes(b"old")

    with pytest.raises(FileExistsError, match="partial prior result"):
        downloader.download_task(
            task,
            api_key="secret",
            email="user@test.cl",
            output_dir=tmp_path,
            session=FakeSession([]),
        )


def test_download_overwrite_replaces_complete_pair(tmp_path: Path) -> None:
    task = make_task()
    csv_path, metadata_path = downloader.output_paths(task, tmp_path)
    csv_path.parent.mkdir(parents=True)
    csv_path.write_bytes(b"old csv")
    metadata_path.write_text("old metadata", encoding="utf-8")

    result = downloader.download_task(
        task,
        api_key="secret",
        email="user@test.cl",
        output_dir=tmp_path,
        overwrite=True,
        session=FakeSession([FakeResponse()]),
    )

    assert result.downloaded
    assert csv_path.read_bytes() == RESOURCE_CSV
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["schema_version"] == 1


@pytest.mark.parametrize("status_code", [400, 500])
def test_download_rejects_http_errors_without_writing(tmp_path: Path, status_code: int) -> None:
    task = make_task()
    with pytest.raises(downloader.NLRDownloadError, match=f"HTTP {status_code}"):
        downloader.download_task(
            task,
            api_key="secret",
            email="user@test.cl",
            output_dir=tmp_path,
            session=FakeSession([FakeResponse(status_code=status_code)]),
        )

    assert not downloader.output_paths(task, tmp_path)[0].exists()


def test_download_reports_timeout_without_writing(tmp_path: Path) -> None:
    task = make_task()
    with pytest.raises(downloader.NLRDownloadError, match="timed out"):
        downloader.download_task(
            task,
            api_key="secret",
            email="user@test.cl",
            output_dir=tmp_path,
            session=FakeSession([requests.Timeout("slow")]),
        )

    assert not downloader.output_paths(task, tmp_path)[0].exists()


def test_download_rejects_non_csv_success_body(tmp_path: Path) -> None:
    task = make_task()
    with pytest.raises(downloader.NLRDownloadError, match="not a recognizable"):
        downloader.download_task(
            task,
            api_key="secret",
            email="user@test.cl",
            output_dir=tmp_path,
            session=FakeSession(
                [FakeResponse(content=b'{"error":"bad request"}', content_type="application/json")]
            ),
        )

    assert not downloader.output_paths(task, tmp_path)[0].exists()


def test_get_credentials_rephrases_missing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_key() -> str:
        raise ValueError("missing")

    monkeypatch.setattr(downloader, "get_nlr_developer_api_key", missing_key)

    with pytest.raises(ValueError, match="NLR_API_KEY and NLR_API_EMAIL"):
        downloader.get_credentials()


def test_main_requests_each_resource_and_year_individually(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_session = FakeSession([FakeResponse() for _ in range(4)])
    monkeypatch.setattr(downloader.requests, "Session", lambda: fake_session)
    monkeypatch.setattr(downloader, "get_credentials", lambda: ("secret", "user@test.cl"))

    exit_code = downloader.main(
        [
            "--site",
            "test_site",
            "--lat",
            "-22.0",
            "--lon",
            "-69.0",
            "--years",
            "2022",
            "2023",
            "--resource",
            "both",
            "--output",
            str(tmp_path),
            "--request-delay",
            "0",
        ]
    )

    assert exit_code == 0
    assert [call[0] for call in fake_session.calls] == [
        downloader.SUP3RWIND_ENDPOINT,
        downloader.NSRDB_ENDPOINT,
        downloader.SUP3RWIND_ENDPOINT,
        downloader.NSRDB_ENDPOINT,
    ]
    assert [call[1]["names"] for call in fake_session.calls] == [
        "2022",
        "2022",
        "2023",
        "2023",
    ]
