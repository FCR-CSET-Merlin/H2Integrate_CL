"""Structural tests for the two Chilean hybrid hydrogen DOE cases."""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

from h2integrate.core.file_utils import load_yaml
from h2integrate.core.inputs.validation import (
    load_driver_yaml,
    load_plant_yaml,
    load_tech_yaml,
)


CASE_DIR = Path(__file__).parents[1] / "chile_hybrid_h2_doe"


def _load_example_module(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, CASE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_doe_has_72_expected_unique_designs():
    cases = pd.read_csv(CASE_DIR / "chile_doe_cases.csv")
    assert len(cases) == 72
    assert not cases.duplicated().any()
    assert set(cases["solar.system_capacity_DC"]) == {100000, 200000, 300000, 400000}
    assert set(cases["wind.num_turbines"]) == {10, 20, 30}
    assert set(cases["electrolyzer.n_clusters"]) == {10, 15, 20, 25, 30, 40}


@pytest.mark.unit
def test_common_and_site_yaml_files_validate():
    load_driver_yaml(CASE_DIR / "common" / "driver_config.yaml")
    load_tech_yaml(CASE_DIR / "common" / "tech_config.yaml")
    for site in ("site_01_antofagasta", "site_02_magallanes"):
        main = load_yaml(CASE_DIR / site / f"{site}.yaml")
        assert main["technology_config"] == "../common/tech_config.yaml"
        plant = load_plant_yaml(CASE_DIR / site / "plant_config.yaml")
        assert plant["plant"]["plant_life"] == 30
        assert plant["plant"]["simulation"]["timezone"] == 0
        solar_resource = plant["sites"]["site"]["resources"]["solar_resource"]
        assert solar_resource["resource_model"] == "GOESFullDiscSolarAPI"
        assert "goes_full_disc_v4" in solar_resource["resource_parameters"]["resource_filename"]


@pytest.mark.unit
def test_prepared_manifest_is_complete_and_ready_for_publication():
    downloader = _load_example_module("chile_doe_download_resources", "download_resources.py")
    manifest = load_yaml(CASE_DIR / "resource_manifest.yaml")
    downloader.validate_manifest(manifest, require_published=False)
    downloader.validate_manifest(manifest, require_published=True)
    assert manifest["release_status"] == "prepared"
    assert manifest["release_tag"] == "chile-weather-2023-v1"


@pytest.mark.unit
def test_conservative_finance_is_merged_without_mutation():
    _load_example_module("download_resources", "download_resources.py")
    runner = _load_example_module("chile_doe_run_case_study", "run_case_study.py")
    config = load_yaml(CASE_DIR / "common" / "financial_parameters.yaml")
    active_case, finance = runner.build_finance_parameters(config)
    params = finance["finance_groups"][active_case]["model_inputs"]["params"]
    capital_items = finance["finance_groups"][active_case]["model_inputs"][
        "capital_items"
    ]
    assert active_case == "conservative"
    assert params["discount_rate"] == pytest.approx(0.10)
    assert params["total_income_tax_rate"] == pytest.approx(0.27)
    assert capital_items["depr_type"] == "Straight line"
    assert capital_items["depr_period"] == 15
    assert "description" in config["cases"]["conservative"]
