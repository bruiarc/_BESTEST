#!/usr/bin/env python3
"""Recast Case 900 as the Case 600 LBNL-report template, retaining Case 900 data."""
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks" / "01_case600_pilot_validation.ipynb"
TARGET = ROOT / "notebooks" / "02_case900_validation.ipynb"


def main() -> None:
    notebook = nbformat.read(SOURCE, as_version=4)
    notebook.cells[0].source = "# BESTEST LBNL-style report — Case 900\n\nNative Python ISO results may be used for formal ASHRAE annual-energy assessment. `modelica_solar` is a controlled-forcing comparison and is not formal pass/fail."
    setup = notebook.cells[1].source
    setup = setup.replace("run_case600_pilot.py", "run_case900_validation.py")
    setup = setup.replace("case = '600'", "case = '900'")
    setup = setup.replace("f'case{case}_feb1_load_profile.csv'", "f'case{case}_feb1_load_profile.csv'")
    notebook.cells[1].source = setup
    notebook.cells[2].source = "## 1. Annual heating energy\n\nAnnual heating energy for the implemented conditioned case, in MWh."
    notebook.cells[4].source = "## 2. Annual cooling energy\n\nAnnual cooling energy for the implemented conditioned case, in MWh."
    notebook.cells[6].source = "## 3. Peak heating load\n\nPeak heating load and completed-hour occurrence time, in kW."
    notebook.cells[8].source = "## 4. Peak cooling load\n\nPeak cooling load and completed-hour occurrence time, in kW."
    notebook.cells[10].source = "## 5. Daily load profile\n\nCase 900 heating and cooling hourly averages on 1 February, plotted at completed hours 1–24. Completed hour 1 represents 00:00–01:00 and hour 24 represents 23:00–24:00; neither track is shifted."
    notebook.cells[11].source = '''profile = daily_slice(selected_hourly(hourly, ISO_MODE), 2, 1)
profile['run'] = profile.implementation.map({'modelica': MODELICA_LABEL, 'iso13790': ISO_LABEL})
fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
for run, frame in profile.groupby('run'):
    frame = frame.sort_values('hour')
    axes[0].plot(frame.hour, frame.heating_load_W / 1000, marker='o', markersize=3, linewidth=1.2, label=run)
    axes[1].plot(frame.hour, frame.cooling_load_W / 1000, marker='o', markersize=3, linewidth=1.2, label=run)
axes[0].set(ylabel='Heating (kW)', title='Case 900: 1 February load profile')
axes[1].set(xlabel='Hour of Day', ylabel='Cooling (kW)', xlim=(1, 24), xticks=range(1, 25))
for axis in axes: axis.grid(alpha=.25); axis.legend(loc='upper center', ncol=2, fontsize=8, frameon=False)
fig.tight_layout(); plt.show()'''
    notebook.cells[12].source = "## Summary\n\nCurrent Case 900 annual-energy record; the main report uses the selected `ISO_MODE`."
    summary = notebook.cells[13].source
    summary = summary.replace("Controlled-forcing ISO is close to Modelica; native ISO remains affected by the unresolved solar-preprocessing discrepancy.", "Controlled-forcing ISO is close to Modelica; native ISO remains affected by the unresolved solar-preprocessing discrepancy.")
    notebook.cells[13].source = summary
    nbf = nbformat.v4
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
            cell.id = nbf.new_code_cell().id
    nbformat.write(notebook, TARGET)


if __name__ == "__main__":
    main()
