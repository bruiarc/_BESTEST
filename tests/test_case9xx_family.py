from pathlib import Path
import json
import math
import nbformat
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "modelica_test_2"))
from iso_validation.bestest_pipeline import CASE_DEFINITIONS
CASES = ("910", "920", "930", "940", "950", "980", "985", "995")
NOTEBOOKS = ("02a", "02b", "02c", "02d", "02e", "02f", "02g", "02h")


def test_case9xx_deltas_and_outputs_are_complete():
    deltas = json.loads((ROOT / "inputs" / "case9xx_deltas.json").read_text())["cases"]
    assert set(CASES).issubset(deltas)
    for case in CASES:
        assert CASE_DEFINITIONS[case].modelica_class == f"Buildings.ThermalZones.ISO13790.Validation.BESTEST.Cases9xx.Case{case}"
        out = ROOT / "results" / f"case{case}"
        native = pd.read_csv(out / f"case{case}_iso13790_native_hourly.csv")
        diagnostic = pd.read_csv(out / f"case{case}_iso13790_diagnostic_modelica_solar_hourly.csv")
        modelica = pd.read_csv(ROOT.parent / "_modelica" / "results" / f"Case{case}" / f"Case{case}_standardized_hourly.csv")
        assert len(native) == len(diagnostic) == len(modelica) == 8760
        assert native.run_mode.eq("native").all()
        assert diagnostic.run_mode.eq("diagnostic_modelica_solar").all()
        metrics = pd.read_csv(out / f"case{case}_metrics.csv")
        assert metrics.value.map(math.isfinite).all()
        assert pd.read_csv(out / f"case{case}_solar_comparison.csv").value.map(math.isfinite).all()


def test_case9xx_notebooks_have_executed_tables_and_figures():
    for case, prefix in zip(CASES, NOTEBOOKS):
        notebook = nbformat.read(ROOT / "notebooks" / f"{prefix}_case{case}_validation.ipynb", as_version=4)
        outputs = [output for cell in notebook.cells for output in cell.get("outputs", [])]
        assert len(notebook.cells) >= 25
        assert any("text/html" in output.get("data", {}) for output in outputs)
        assert sum("image/png" in output.get("data", {}) for output in outputs) >= 4
