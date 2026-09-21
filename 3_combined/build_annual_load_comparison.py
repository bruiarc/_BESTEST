#!/usr/bin/env python3
"""Create combined BESTEST annual-load tables and plots from cached CSVs only.

No Modelica, ISO 13790, or VDI model is executed by this script.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "600", "610", "620", "630", "640", "650", "660", "670", "680", "685",
    "695", "900", "910", "920", "930", "940", "950", "980", "985", "995",
)
PROGRAMS = ("BSIMAC", "CSE", "DeST", "EnergyPlus", "ESP-r", "TRNSYS")
OUTCOMES = ("LBNL-5R1C", "5R1C", "7R2C")
TABLE_COLUMNS = ("Case", "Lower limit", "Upper limit", *PROGRAMS, *OUTCOMES)


def read_reference_table(metric: str) -> pd.DataFrame:
    """Parse the annual reference table embedded in the local Markdown file."""
    heading = (
        "# 3. Annual heating energy reference data"
        if metric == "heating"
        else "# 4. Annual cooling energy reference data"
    )
    lines = (ROOT / "reference" / "BESTEST_LBNL_EUI.md").read_text().splitlines()
    start = lines.index(heading)
    header_index = next(i for i in range(start, len(lines)) if lines[i].startswith("| Case |"))
    headers = [item.strip() for item in lines[header_index].strip("|").split("|")]
    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append([item.strip() for item in line.strip("|").split("|")])
    table = pd.DataFrame(rows, columns=headers)
    table["Case"] = table["Case"].astype(str).str.zfill(3)
    for column in headers[1:]:
        table[column] = pd.to_numeric(table[column], errors="raise")
    return table.set_index("Case").loc[list(CASES)].reset_index()


def iso_values(metric: str) -> pd.Series:
    """Read the specified controlled-solar 5R1C annual metric from cached ISO CSVs."""
    metric_name = f"annual_{metric}_energy"
    values: dict[str, float] = {}
    for case in CASES:
        path = ROOT / "results" / "1_iso" / f"case{case}" / f"case{case}_metrics.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Cached ISO result is missing: {path}")
        data = pd.read_csv(path, dtype={"case": str})
        selected = data.loc[
            (data["implementation"] == "iso13790")
            & (data["run_mode"] == "diagnostic_modelica_solar")
            & (data["metric"] == metric_name),
            "value",
        ]
        if len(selected) != 1:
            raise ValueError(f"Expected one controlled-solar ISO value for Case {case}, {metric}")
        values[case] = float(selected.iloc[0])
    return pd.Series(values, name="5R1C")


def vdi_values(metric: str) -> pd.Series:
    """Read the specified F36 (7R2C) annual metric from the cached VDI CSV."""
    path = ROOT / "results" / "2_vdi" / "bestest_6xx_9xx_ashrae140_layers" / "annual_results.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Cached VDI result is missing: {path}")
    data = pd.read_csv(path, dtype={"case": str})
    data["case"] = data["case"].str.zfill(3)
    column = f"{metric}_MWh"
    selected = data.loc[data["configuration"] == "F36-like", ["case", column]]
    if selected["case"].duplicated().any() or set(selected["case"]) != set(CASES):
        raise ValueError("Expected exactly one F36-like VDI result for every BESTEST case")
    return selected.set_index("case").loc[list(CASES), column].rename("7R2C")


def build_comparison() -> pd.DataFrame:
    """Build the persistent comparison table from the three requested outcomes."""
    frames: list[pd.DataFrame] = []
    for metric in ("heating", "cooling"):
        reference = read_reference_table(metric).set_index("Case")
        result = reference[["Lower", "Upper", *PROGRAMS, "Modelica ISO13790"]].copy()
        result = result.rename(columns={"Modelica ISO13790": "LBNL-5R1C"})
        result["5R1C"] = iso_values(metric)
        result["7R2C"] = vdi_values(metric)
        result.insert(0, "metric", metric)
        result.insert(0, "case", result.index)
        result = result.rename(columns={"Lower": "lower_MWh", "Upper": "upper_MWh"})
        result["bounds_valid"] = result["lower_MWh"] <= result["upper_MWh"]
        for outcome in OUTCOMES:
            result[f"{outcome}_in_range"] = np.where(
                result["bounds_valid"],
                result[outcome].between(result["lower_MWh"], result["upper_MWh"]),
                pd.NA,
            )
        frames.append(result.reset_index(drop=True))
    return pd.concat(frames, ignore_index=True)


def draw_table(ax: plt.Axes, metric: str, comparison: pd.DataFrame) -> None:
    data = comparison.loc[comparison.metric == metric].set_index("case").loc[list(CASES)]
    rows: list[list[str]] = []
    red_cells: list[tuple[int, int]] = []
    programs_and_outcomes = (*PROGRAMS, *OUTCOMES)
    for row_number, (case, item) in enumerate(data.iterrows(), start=1):
        values = [f"Case{case}", f"{item.lower_MWh:.2f}", f"{item.upper_MWh:.2f}"]
        values += [f"{item[column]:.3f}" for column in programs_and_outcomes]
        rows.append(values)
        if bool(item.bounds_valid):
            for column_number, column in enumerate(programs_and_outcomes, start=3):
                if not item.lower_MWh <= item[column] <= item.upper_MWh:
                    red_cells.append((row_number, column_number))
    table = ax.table(cellText=rows, colLabels=TABLE_COLUMNS, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(6.0)
    table.scale(1.0, 1.24)
    for column in range(len(TABLE_COLUMNS)):
        table[(0, column)].set_facecolor("#808080")
        table[(0, column)].set_text_props(color="white", weight="bold")
    for row, column in red_cells:
        table[(row, column)].set_facecolor("#ff4b0b")
    ax.set_title(f"Annual {metric} load (MWh)", loc="left", fontsize=13, weight="bold", color="#103b5b")
    ax.axis("off")


def draw_columns(ax: plt.Axes, metric: str, comparison: pd.DataFrame) -> None:
    data = comparison.loc[comparison.metric == metric].set_index("case").loc[list(CASES)]
    x = np.arange(len(data))
    ax.fill_between(x, data.lower_MWh, data.upper_MWh, color="#d8e5eb", step="mid", label="Acceptance range")
    colors = {"LBNL-5R1C": "#103b5b", "5R1C": "#347c98", "7R2C": "#7851a9"}
    width = 0.23
    for index, outcome in enumerate(OUTCOMES):
        positions = x + (index - 1) * width
        in_range = data[outcome].between(data.lower_MWh, data.upper_MWh) & data.bounds_valid
        colors_for_bars = np.where(in_range, colors[outcome], "#ff4b0b")
        ax.bar(positions, data[outcome], width=width, color=colors_for_bars, label=outcome, zorder=3)
    ax.plot(x, data.lower_MWh, color="#536a78", linewidth=0.9, zorder=4)
    ax.plot(x, data.upper_MWh, color="#536a78", linewidth=0.9, zorder=4)
    ax.set_xticks(x, [f"{case}" for case in CASES], rotation=45, ha="right")
    ax.set_ylabel("MWh")
    ax.set_title(f"Annual {metric} load: selected model outcomes", loc="left", color="#103b5b", weight="bold")
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def render(comparison: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output_dir / "annual_load_comparison.csv", index=False)

    figure, axes = plt.subplots(2, 1, figsize=(18, 17.2))
    for axis, metric in zip(axes, ("heating", "cooling")):
        draw_table(axis, metric, comparison)
    figure.tight_layout(h_pad=1.1)
    figure.savefig(output_dir / "BESTEST_LBNL_EUI_5R1C_7R2C.png", dpi=220, bbox_inches="tight")
    plt.close(figure)

    figure, axes = plt.subplots(2, 1, figsize=(17, 10), sharex=True)
    for axis, metric in zip(axes, ("heating", "cooling")):
        draw_columns(axis, metric, comparison)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output_dir / "BESTEST_LBNL_EUI_5R1C_7R2C_columns.png", dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "3_combined" / "outputs")
    args = parser.parse_args()
    comparison = build_comparison()
    render(comparison, args.output_dir)
    valid = comparison.loc[comparison.bounds_valid]
    print(f"Wrote cached comparison for {len(comparison)} case/metric rows to {args.output_dir}")
    for outcome in OUTCOMES:
        print(f"{outcome}: {(valid[f'{outcome}_in_range'] == False).sum()} out-of-range values")
    print(f"Rows with malformed benchmark bounds: {(~comparison.bounds_valid).sum()}")


if __name__ == "__main__":
    main()
