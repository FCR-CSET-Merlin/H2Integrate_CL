"""Download and verify public meteorological assets for the Chilean DOE cases."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from h2integrate.core.file_utils import load_yaml


THIS_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = THIS_DIR / "resource_manifest.yaml"
DEFAULT_DATA_DIR = THIS_DIR / "data"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sha256sum(filepath: Path) -> str:
    """Return the hexadecimal SHA-256 digest of a local file."""
    digest = hashlib.sha256()
    with filepath.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(manifest: dict[str, Any], *, require_published: bool) -> None:
    """Validate manifest structure and optionally require downloadable assets."""
    if manifest.get("schema_version") != 1:
        raise ValueError("resource_manifest.yaml must use schema_version: 1.")
    resources = manifest.get("resources")
    if not isinstance(resources, list) or len(resources) != 4:
        raise ValueError("The manifest must contain exactly four resource entries.")

    filenames: set[str] = set()
    site_kinds: set[tuple[str, str]] = set()
    for resource in resources:
        filename = resource.get("filename")
        if not filename or Path(filename).name != filename:
            raise ValueError("Every resource filename must be a safe basename.")
        if filename in filenames:
            raise ValueError(f"Duplicate resource filename: {filename}.")
        filenames.add(filename)
        site_kinds.add((resource.get("site"), resource.get("kind")))

        if not require_published:
            continue
        url = resource.get("url")
        checksum = resource.get("sha256")
        size_bytes = resource.get("size_bytes")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError(f"Resource {filename} has no published HTTPS URL.")
        if not isinstance(checksum, str) or SHA256_PATTERN.fullmatch(checksum) is None:
            raise ValueError(f"Resource {filename} has no valid SHA-256 checksum.")
        if not isinstance(size_bytes, int) or size_bytes <= 0:
            raise ValueError(f"Resource {filename} has no valid byte size.")

    expected_site_kinds = {
        (site, kind)
        for site in ("site_01_antofagasta", "site_02_magallanes")
        for kind in ("wind", "solar")
    }
    if site_kinds != expected_site_kinds:
        raise ValueError("The manifest must define wind and solar data for both sites.")


def verify_file(filepath: Path, resource: dict[str, Any]) -> None:
    """Verify file size and SHA-256 against a published manifest entry."""
    actual_size = filepath.stat().st_size
    if actual_size != resource["size_bytes"]:
        raise ValueError(
            f"Size mismatch for {filepath.name}: {actual_size} != {resource['size_bytes']}."
        )
    actual_checksum = sha256sum(filepath)
    if actual_checksum != resource["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {filepath.name}.")


def verify_resources(
    manifest_path: Path = DEFAULT_MANIFEST,
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    sites: set[str] | None = None,
) -> None:
    """Require all selected local assets to exist and match the manifest."""
    manifest = load_yaml(manifest_path)
    validate_manifest(manifest, require_published=True)
    selected = [
        resource
        for resource in manifest["resources"]
        if sites is None or resource["site"] in sites
    ]
    for resource in selected:
        filepath = data_dir / resource["filename"]
        if not filepath.is_file():
            raise FileNotFoundError(
                f"Missing meteorological resource {filepath}. Run download_resources.py."
            )
        verify_file(filepath, resource)


def download_resources(
    manifest_path: Path = DEFAULT_MANIFEST,
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    force: bool = False,
) -> None:
    """Download all assets atomically and verify them before installation."""
    manifest = load_yaml(manifest_path)
    validate_manifest(manifest, require_published=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    for resource in manifest["resources"]:
        destination = data_dir / resource["filename"]
        if destination.is_file() and not force:
            verify_file(destination, resource)
            print(f"verified {destination}")
            continue

        temporary = destination.with_suffix(destination.suffix + ".part")
        try:
            with urllib.request.urlopen(resource["url"]) as response:  # noqa: S310
                with temporary.open("wb") as stream:
                    shutil.copyfileobj(response, stream)
            verify_file(temporary, resource)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"downloaded {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_resources(args.manifest, args.data_dir)
    else:
        download_resources(args.manifest, args.data_dir, force=args.force)


if __name__ == "__main__":
    main()
