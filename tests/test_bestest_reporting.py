from pathlib import Path
import json
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bestest_reporting import annual_energy_table, daily_slice, peak_table, selected_hourly, selected_iso_mode  # noqa: E402


def test_lbnl_report_helpers_switch_iso_track_without_hard_coded_results():
    metrics = pd.read_csv(ROOT / "results/case600/case600_metrics.csv")
    reference = ROOT / "_ref/BESTEST_LBNL_all_cases_reference.md"
    controlled = annual_energy_table(metrics, reference, "600", "annual_cooling_energy", "modelica_solar")
    native = annual_energy_table(metrics, reference, "600", "annual_cooling_energy", "native")
    assert selected_iso_mode("modelica_solar")[0] == "diagnostic_modelica_solar"
    assert controlled["Python range status"].iloc[0] == "PASS — diagnostic"
    assert native["Python range status"].iloc[0] == "FAIL"
    assert controlled["RClib-ISO + Modelica-resolved solar"].iloc[0] > 5
    assert native["RClib-ISO native solar"].iloc[0] < 2
    peak = peak_table(metrics, reference, "600", "peak_cooling_load", "modelica_solar")
    assert "22-Jan:14" in peak["Modelica native"].iloc[0]


def test_pilot_notebook_has_only_current_lbnl_conditioned_categories():
    notebook = json.loads((ROOT / "notebooks/01_case600_pilot_validation.ipynb").read_text())
    headings = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "markdown"]
    text = "\n".join(headings)
    for heading in ("Annual heating energy", "Annual cooling energy", "Peak heating load", "Peak cooling load", "Daily load profile"):
        assert heading in text
    assert "Heating-discrepancy attribution" not in text
    assert "Case600FF regression" not in text


def test_daily_slice_uses_datetime_series_accessor_for_february_profile():
    hourly = pd.read_csv(ROOT / "results/case600/case600_feb1_load_profile.csv")
    profile = daily_slice(selected_hourly(hourly, "modelica_solar"), 2, 1)
    assert len(profile) == 48
    assert set(profile.hour) == set(range(1, 25))


def test_timestamp_audit_has_common_completed_hour_grid():
    subprocess.run([sys.executable, "scripts/audit_case600_timestamps.py", "--iso-mode", "modelica_solar"], cwd=ROOT, check=True)
    audit = pd.read_csv(ROOT / "results/case600/case600_feb1_timestamp_alignment_modelica_solar.csv")
    assert len(audit) == 24
    assert audit.modelica_completed_hour.tolist() == list(range(1, 25))
    assert audit.iso_completed_hour.tolist() == list(range(1, 25))
    assert (audit.modelica_raw_timestamp == audit.iso_raw_timestamp).all()
