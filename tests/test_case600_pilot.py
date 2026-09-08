from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pilot_output(tmp_path_factory):
    out = tmp_path_factory.mktemp("case600-pilot")
    subprocess.run([sys.executable, "scripts/run_case600_pilot.py", "--output", str(out)], cwd=ROOT, check=True)
    return out


def test_case600_input_and_mapping_are_complete():
    data = __import__("json").loads((ROOT / "inputs" / "case600.json").read_text())
    assert data["case"] == "600" and data["geometry"]["floor_area_m2"] == 48.0
    mapping = pd.read_csv(ROOT / "inputs" / "case600_adapter_mapping.csv")
    assert {"direct", "derived", "aggregated", "implementation_specific"}.issubset(mapping.mapping_type)
    assert mapping.modelica_value.notna().all() and mapping.iso_value.notna().all()


def test_standard_outputs_separate_native_and_diagnostic(pilot_output):
    out = pilot_output
    native = pd.read_csv(out / "case600_iso13790_native_hourly.csv")
    diagnostic = pd.read_csv(out / "case600_iso13790_diagnostic_modelica_solar_hourly.csv")
    assert len(native) == len(diagnostic) == 8760
    assert native.run_mode.eq("native").all() and native.formal_ashrae_result.all()
    assert diagnostic.run_mode.eq("diagnostic_modelica_solar").all()
    assert not diagnostic.formal_ashrae_result.any()
    assert native.timestamp_s.iloc[0] == 3600 and native.timestamp_s.iloc[-1] == 31536000


def test_case600_annual_metrics_and_manifest(pilot_output):
    out = pilot_output
    formal = pd.read_csv(out / "case600_formal_ashrae_energy.csv")
    assert set(formal.metric) == {"annual_heating_energy", "annual_cooling_energy"}
    assert set(formal.implementation) == {"modelica", "iso13790"}
    assert formal.loc[formal.implementation.eq("modelica"), "within_ashrae_range"].all()
    assert len(pd.read_csv(out / "manifest.csv")) == 10
    profile = pd.read_csv(out / "case600_feb1_load_profile.csv")
    assert len(profile) == 24 * 3 and set(profile.run_mode) == {"native", "diagnostic_modelica_solar"}


def test_case600ff_diagnostic_regression_is_computed(pilot_output):
    out = pilot_output
    regression = pd.read_csv(out / "case600ff_regression_summary.csv")
    assert regression.loc[0, "Rows"] == 8760
    assert regression.loc[0, "mae_C"] > 0
    assert regression.loc[0, "formal_ashrae_result"] == False
