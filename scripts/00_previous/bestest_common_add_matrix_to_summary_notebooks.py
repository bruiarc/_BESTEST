#!/usr/bin/env python3
"""Append the LBNL-style annual matrix directly to each family summary notebook."""
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "01_cases6xx_summary.ipynb": ("600", "610", "620", "630", "640", "650", "660", "670", "680", "685", "695"),
    "02_cases9xx_summary.ipynb": ("900", "910", "920", "930", "940", "950", "980", "985", "995"),
}


def main() -> None:
    for name, cases in TARGETS.items():
        path = ROOT / "notebooks" / name
        notebook = nbformat.read(path, as_version=4)
        notebook.cells = [cell for cell in notebook.cells if "Annual ASHRAE 140 matrix" not in cell.source]
        literal = repr(cases)
        notebook.cells.extend([
            nbformat.v4.new_markdown_cell("## Annual ASHRAE 140 matrix\n\nLBNL-style annual heating and cooling tables. Red cells are outside valid published acceptance bounds; native ISO is the formal Python result."),
            nbformat.v4.new_code_cell(f'''from bestest_iso_plot_ashrae140_annual_matrix import build_summary, draw_table
matrix = build_summary()
family_cases = {literal}
fig, axes = plt.subplots(2, 1, figsize=(15, 10.5))
draw_table(axes[0], 'heating', matrix, family_cases)
draw_table(axes[1], 'cooling', matrix, family_cases)
fig.tight_layout(); plt.show()
display(matrix[matrix.case.isin(family_cases)][['case', 'metric', 'actual_modelica_MWh', 'rclib_iso_modelica_solar_MWh', 'actual_modelica_status']])'''),
        ])
        nbformat.write(notebook, path)


if __name__ == "__main__":
    main()
