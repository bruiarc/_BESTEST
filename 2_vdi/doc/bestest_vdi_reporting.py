"""Compact, registry-driven reporting for the VDI BESTEST notebook set."""

from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import pandas as pd

try:
    from . import bestest_vdi_transfer_engine as engine
except ImportError:  # direct execution with doc/ on sys.path
    import bestest_vdi_transfer_engine as engine

RESULTS = engine.VDI / "results/bestest_6xx_9xx_ashrae140_layers/annual_results.csv"
PRIMARY_PARENT = {
    "600": None, "610": "600", "620": "600", "630": "620", "640": "600",
    "650": "600", "660": "600", "670": "600", "680": "600", "685": "600",
    "695": "680", "900": "600", "910": "900", "920": "900", "930": "920",
    "940": "900", "950": "900", "980": "900", "985": "900", "995": "980",
}


def annual_results() -> pd.DataFrame:
    data = pd.read_csv(RESULTS, dtype={"case": str})
    data["case"] = data["case"].str.zfill(3)
    return data


def case_definition(case: str) -> pd.DataFrame:
    row = engine.case_matrix().query("case_id == @case").copy()
    return row[["case_id", "paired_case", "parent_base", "physical_change",
                "implementation_class", "iso_notebook"]].reset_index(drop=True)


def resolved_input_mapping(case: str) -> pd.DataFrame:
    d = engine._configure_defaults(case)
    opaque = d["opaque_elements"]
    glazing = d["glazing_convention"]
    rows = [
        ("opaque construction", d["material_convention"]["envelope_case"],
         "ashrae140_case_constructions.json"),
        ("wall / roof / floor U [W/(m2 K)]",
         f"{d['u_walls']:.3g} / {next(x['u_value'] for x in opaque if x['name']=='roof'):.3g} / "
         f"{next(x['u_value'] for x in opaque if x['name']=='floor'):.3g}",
         "prescribed transmission inputs"),
        ("window system", glazing["id"], "ashrae140_case_constructions.json"),
        ("window U / g", f"{d['u_windows']:.3g} / {d['glass_solar_transmittance']:.3g}",
         glazing.get("whole_window_u_source", glazing["ashrae_table"])),
        ("window orientation / area",
         ", ".join(f"{x['name']}: {x['area_m2']:g} m2" for x in d["window_elements"]),
         "central case registry"),
        ("shading factor", f"{d['window_elements'][0]['F_sh_ob']:.4g}", "central case registry"),
        ("thermostat / airflow delta", "; ".join(engine._case_changes(case)) or "base",
         "BESTEST case delta registry"),
    ]
    return pd.DataFrame(rows, columns=["VDI input", "resolved value", "provenance"])


def static_checks(case: str) -> pd.DataFrame:
    engine.validate_case_registry()
    d = engine._configure_defaults(case)
    film_free_r = 1 / d["u_windows"] - 1 / 8 - 1 / 25
    checks = [
        ("authoritative material convention", d["material_convention"]["primary"] == "ashrae140_layers"),
        ("three opaque assemblies resolved", len(d["constructions"]) == 3),
        ("window area is 12 m2", math.isclose(sum(x["area_m2"] for x in d["window_elements"]), 12.0)),
        ("positive film-excluded glazing resistance", film_free_r > 0),
        ("finite layer properties", np.isfinite(engine.layer_audit(d).select_dtypes("number")).all().all()),
    ]
    return pd.DataFrame(checks, columns=["check", "pass"])


def annual_validation(case: str) -> pd.DataFrame:
    cols = ["configuration", "heating_MWh", "cooling_MWh", "heating_in_range",
            "cooling_in_range", "both_in_range", "D_MWh_norm",
            "maximum_balance_residual_W"]
    return annual_results().query("case == @case")[cols].reset_index(drop=True)


def parent_response(case: str) -> pd.DataFrame:
    parent = PRIMARY_PARENT[case]
    if parent is None:
        return pd.DataFrame([{"case": case, "parent": "base case", "interpretation":
                              "Reference point for parent-relative comparisons."}])
    data = annual_results()
    child = data.query("case == @case").set_index("configuration")
    base = data.query("case == @parent").set_index("configuration")
    rows = []
    for cfg in child.index:
        dh = child.at[cfg, "heating_MWh"] - base.at[cfg, "heating_MWh"]
        dc = child.at[cfg, "cooling_MWh"] - base.at[cfg, "cooling_MWh"]
        rows.append({"configuration": cfg, "parent": parent,
                     "heating_delta_MWh": dh, "cooling_delta_MWh": dc,
                     "interpretation": f"Heating {'increases' if dh>0 else 'decreases' if dh<0 else 'is unchanged'}; "
                     f"cooling {'increases' if dc>0 else 'decreases' if dc<0 else 'is unchanged'} versus Case {parent}."})
    return pd.DataFrame(rows)


def family_summary(family: str) -> pd.DataFrame:
    cases = [c for c in engine.ALL_CASES if c.startswith(family[0])]
    data = annual_results().query("case in @cases").copy()
    parents = []
    dh, dc = [], []
    for _, row in data.iterrows():
        parent = PRIMARY_PARENT[row.case]
        parents.append(parent or "base")
        if parent is None:
            dh.append(0.0); dc.append(0.0)
        else:
            ref = data[(data.case == parent) & (data.configuration == row.configuration)]
            if ref.empty:
                all_data = annual_results()
                ref = all_data[(all_data.case == parent) &
                               (all_data.configuration == row.configuration)]
            dh.append(row.heating_MWh - ref.heating_MWh.iloc[0])
            dc.append(row.cooling_MWh - ref.cooling_MWh.iloc[0])
    data["parent"] = parents
    data["heating_delta_MWh"] = dh
    data["cooling_delta_MWh"] = dc
    return data[["case", "configuration", "heating_MWh", "cooling_MWh",
                 "heating_in_range", "cooling_in_range", "both_in_range",
                 "parent", "heating_delta_MWh", "cooling_delta_MWh"]]


def combined_summary() -> pd.DataFrame:
    return pd.concat([family_summary("6xx"), family_summary("9xx")], ignore_index=True)


def unresolved_benchmark_issues() -> pd.DataFrame:
    data = annual_results()
    bad = data.loc[~data.bounds_valid.astype(bool),
                   ["case", "lower_heating", "upper_heating", "lower_cooling", "upper_cooling"]]
    return bad.drop_duplicates().assign(issue="invalid/reversed benchmark bounds; pass/fail withheld")
