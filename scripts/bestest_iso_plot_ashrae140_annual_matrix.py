#!/usr/bin/env python3
"""Render LBNL-style annual BESTEST matrices from parsed reference/result data."""
from __future__ import annotations

from pathlib import Path
import sys
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bestest_iso_reporting import markdown_table

CASES = ("600", "610", "620", "630", "640", "650", "660", "670", "680", "685", "695", "900", "910", "920", "930", "940", "950", "980", "985", "995")
PROGRAMS = ("BSIMAC", "CSE", "DeST", "EnergyPlus", "ESP-r", "TRNSYS", "Modelica ISO13790")


def _reference(metric: str) -> pd.DataFrame:
    section = "Annual heating energy reference data" if metric == "heating" else "Annual cooling energy reference data"
    data = markdown_table(ROOT / "_ref" / "BESTEST_LBNL_all_cases_reference.md", section).copy()
    data = data[data.Case.isin(CASES)].set_index("Case").loc[list(CASES)].reset_index()
    for column in ("Lower", "Upper", *PROGRAMS):
        data[column] = pd.to_numeric(data[column])
    return data


def _actual(case: str, implementation: str, mode: str, metric: str) -> float:
    data = pd.read_csv(ROOT / "results" / "1_iso" / f"case{case}" / f"case{case}_metrics.csv")
    key = "annual_heating_energy" if metric == "heating" else "annual_cooling_energy"
    return float(data[(data.implementation == implementation) & (data.run_mode == mode) & (data.metric == key)].value.iloc[0])


def build_summary() -> pd.DataFrame:
    rows = []
    for metric in ("heating", "cooling"):
        reference = _reference(metric)
        for _, item in reference.iterrows():
            valid_bounds = item.Lower <= item.Upper
            published = item["Modelica ISO13790"]
            actual = _actual(item.Case, "modelica", "native", metric)
            native = _actual(item.Case, "iso13790", "native", metric)
            controlled = _actual(item.Case, "iso13790", "diagnostic_modelica_solar", metric)
            rows.append({"case": item.Case, "metric": metric, "lower_MWh": item.Lower, "upper_MWh": item.Upper,
                         "bounds_valid": valid_bounds, "published_lbnl_modelica_MWh": published,
                         "actual_modelica_MWh": actual, "native_iso_MWh": native,
                         "rclib_iso_modelica_solar_MWh": controlled,
                         "modelica_minus_published_MWh": actual - published,
                         "published_lbnl_modelica_status": "PASS" if valid_bounds and item.Lower <= published <= item.Upper else "FAIL" if valid_bounds else "N/A: malformed bounds",
                         "actual_modelica_status": "PASS" if valid_bounds and item.Lower <= actual <= item.Upper else "FAIL" if valid_bounds else "N/A: malformed bounds",
                         "native_iso_status": "PASS" if valid_bounds and item.Lower <= native <= item.Upper else "FAIL" if valid_bounds else "N/A: malformed bounds"})
    return pd.DataFrame(rows)


def draw_table(ax, metric: str, summary: pd.DataFrame, cases: tuple[str, ...] = CASES) -> None:
    reference = _reference(metric)
    reference = reference[reference.Case.isin(cases)]
    subset = summary[summary.metric == metric].set_index("case")
    columns = ["Case", "Lower", "Upper", *PROGRAMS, "Modelica actual", "RClib.iso13790.solar"]
    rows = []
    red = []
    for _, item in reference.iterrows():
        case = item.Case
        values = [f"Case{case}", f"{item.Lower:.2f}", f"{item.Upper:.2f}"] + [f"{item[p]:.3f}" for p in PROGRAMS]
        values += [f"{subset.loc[case, 'actual_modelica_MWh']:.3f}", f"{subset.loc[case, 'rclib_iso_modelica_solar_MWh']:.3f}"]
        rows.append(values)
        for col, program in enumerate(PROGRAMS, start=3):
            if item.Lower <= item.Upper and not (item.Lower <= item[program] <= item.Upper): red.append((len(rows), col))
        if subset.loc[case, "actual_modelica_status"] == "FAIL": red.append((len(rows), 3 + len(PROGRAMS)))
        if item.Lower <= item.Upper and not (item.Lower <= subset.loc[case, "rclib_iso_modelica_solar_MWh"] <= item.Upper): red.append((len(rows), 4 + len(PROGRAMS)))
    table = ax.table(cellText=rows, colLabels=columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False); table.set_fontsize(6.3); table.scale(1, 1.24)
    for col in range(len(columns)):
        table[(0, col)].set_facecolor("#808080"); table[(0, col)].set_text_props(color="white", weight="bold")
    for row, col in red: table[(row, col)].set_facecolor("#ff4b0b")
    ax.set_title(f"Annual {metric} load (MWh)", loc="left", fontsize=12, weight="bold", color="#103b5b")
    ax.axis("off")


def main() -> None:
    summary = build_summary()
    output = ROOT / "results" / "1_iso" / "ashrae140_annual_load_matrix.csv"
    summary.to_csv(output, index=False)
    figure, axes = plt.subplots(2, 1, figsize=(15, 15.5))
    draw_table(axes[0], "heating", summary); draw_table(axes[1], "cooling", summary)
    figure.tight_layout()
    figure.savefig(ROOT / "results" / "1_iso" / "ashrae140_annual_load_matrix.png", dpi=180, bbox_inches="tight")
    valid = summary[summary.bounds_valid]
    print("actual Modelica differs from published LBNL Modelica by max", summary.modelica_minus_published_MWh.abs().max(), "MWh")
    print("published LBNL Modelica red cells:", (valid.published_lbnl_modelica_status == "FAIL").sum())
    print("actual Modelica red cells:", (valid.actual_modelica_status == "FAIL").sum())
    print("native ISO red cells:", (valid.native_iso_status == "FAIL").sum())
    print("malformed acceptance-bound rows:", (~summary.bounds_valid).sum())


if __name__ == "__main__": main()
