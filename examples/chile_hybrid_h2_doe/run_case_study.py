"""Run either or both Chilean hybrid hydrogen DOE cases."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

import openmdao.api as om
import pandas as pd

from download_resources import verify_resources
from h2integrate.core.file_utils import load_yaml
from h2integrate.core.h2integrate_model import H2IntegrateModel


THIS_DIR = Path(__file__).resolve().parent
MINIMUM_HYDROGEN_KG_PER_YEAR = 20_000_000.0
SITE_CONFIGS = {
    "site_01_antofagasta": THIS_DIR
    / "site_01_antofagasta"
    / "site_01_antofagasta.yaml",
    "site_02_magallanes": THIS_DIR
    / "site_02_magallanes"
    / "site_02_magallanes.yaml",
}


def merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two configuration dictionaries without mutating either."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def build_finance_parameters(financial_config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Build H2Integrate finance groups from the selected Chilean scenario."""
    active_case = financial_config["active_case"]
    cases = financial_config["cases"]
    if active_case not in cases:
        raise ValueError(f"Unknown financial case '{active_case}'.")
    selected_config = merge_dicts(financial_config["shared"], cases[active_case])
    selected_config.pop("description", None)
    selected = {
        "finance_model": selected_config.pop("finance_model"),
        "model_inputs": selected_config,
    }

    subgroups = {}
    for name, commodity, stream, technologies in (
        ("solar_electricity", "electricity", "solar", ["solar"]),
        ("wind_electricity", "electricity", "wind", ["wind"]),
        (
            "electricity",
            "electricity",
            "electricity_combiner",
            ["solar", "wind"],
        ),
        (
            "hydrogen",
            "hydrogen",
            "electrolyzer",
            ["solar", "wind", "electrolyzer"],
        ),
    ):
        subgroups[name] = {
            "commodity": commodity,
            "commodity_stream": stream,
            "finance_groups": [active_case],
            "technologies": technologies,
        }
    return active_case, {
        "finance_groups": {active_case: selected},
        "finance_subgroups": subgroups,
        "cost_adjustment_parameters": financial_config["cost_adjustment_parameters"],
    }


def build_model(site: str) -> tuple[str, H2IntegrateModel]:
    """Build one site model with absolute runtime paths and Chilean finance."""
    main_config_path = SITE_CONFIGS[site]
    main_config = load_yaml(main_config_path)
    driver_config = load_yaml(THIS_DIR / "common" / "driver_config.yaml")
    driver_config["driver"]["design_of_experiments"]["filename"] = str(
        THIS_DIR / "chile_doe_cases.csv"
    )
    driver_config["general"]["folder_output"] = str(THIS_DIR / "outputs" / site)

    plant_config = load_yaml(main_config_path.parent / "plant_config.yaml")
    resources = plant_config["sites"]["site"]["resources"]
    for resource in resources.values():
        resource["resource_parameters"]["resource_dir"] = str(THIS_DIR / "data")

    financial_config = load_yaml(THIS_DIR / "common" / "financial_parameters.yaml")
    active_case, finance_parameters = build_finance_parameters(financial_config)
    plant_config["finance_parameters"] = finance_parameters
    runtime_config = {
        "name": main_config["name"],
        "system_summary": main_config["system_summary"],
        "driver_config": driver_config,
        "technology_config": str(THIS_DIR / "common" / "tech_config.yaml"),
        "plant_config": plant_config,
    }
    return active_case, H2IntegrateModel(runtime_config)


def scalar(case: om.Case, name: str, units: str | None = None) -> float:
    """Read an OpenMDAO case value as a scalar float."""
    return float(case.get_val(name, units=units).flat[0])


def collect_results(site: str, active_case: str, cases: list[om.Case]) -> pd.DataFrame:
    """Collect DOE outputs needed to select the minimum feasible LCOH."""
    rows = []
    for case_number, case in enumerate(cases):
        design_variables = case.get_design_vars()
        solar_kwdc = float(design_variables["solar.system_capacity_DC"][0])
        turbine_count = int(round(float(design_variables["wind.num_turbines"][0])))
        cluster_count = int(round(float(design_variables["electrolyzer.n_clusters"][0])))
        rows.append(
            {
                "site": site,
                "financial_case": active_case,
                "doe_case": case_number,
                "solar_MWdc": solar_kwdc / 1000.0,
                "wind_turbines": turbine_count,
                "wind_MW": turbine_count * 6.0,
                "pem_clusters": cluster_count,
                "pem_MW": cluster_count * 10.0,
                "hydrogen_kg_year": scalar(
                    case, "electrolyzer.annual_hydrogen_produced", "kg/year"
                ),
                "pem_capacity_factor": scalar(case, "electrolyzer.capacity_factor"),
                "LCOE_USD_MWh": scalar(
                    case, "finance_subgroup_electricity.LCOE", "USD/(MW*h)"
                ),
                "LCOH_USD_kg": scalar(
                    case, "finance_subgroup_hydrogen.LCOH", "USD/kg"
                ),
            }
        )
    return pd.DataFrame(rows)


def run_site(site: str) -> pd.DataFrame:
    """Validate resources, run 72 designs, save results, and report the best design."""
    verify_resources(sites={site})
    active_case, model = build_model(site)
    model.run()
    model.post_process(print_results=False, summarize_sql=True)
    sql_path = THIS_DIR / "outputs" / site / "cases.sql"
    cases = list(om.CaseReader(sql_path).get_cases())
    results = collect_results(site, active_case, cases)
    output_path = THIS_DIR / "outputs" / site / "doe_results.csv"
    results.to_csv(output_path, index=False)

    feasible = results[results["hydrogen_kg_year"] >= MINIMUM_HYDROGEN_KG_PER_YEAR]
    print(f"{site}: {len(results)} designs; {len(feasible)} satisfy the H2 threshold")
    if not feasible.empty:
        best = feasible.loc[feasible["LCOH_USD_kg"].idxmin()]
        print(best.to_string())
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", choices=[*SITE_CONFIGS, "all"], default="all", nargs="?")
    args = parser.parse_args()
    sites = SITE_CONFIGS if args.site == "all" else (args.site,)
    for site in sites:
        run_site(site)


if __name__ == "__main__":
    main()
