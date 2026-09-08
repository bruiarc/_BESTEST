from pathlib import Path
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_debug_trace_rejects_load_processing_and_flags_solar():
    subprocess.run([sys.executable, "scripts/debug_case600.py"], cwd=ROOT, check=True)
    out = ROOT / "results/case600_debug"
    loads = pd.read_csv(out / "load_extraction_trace.csv")
    assert loads.iloc[1].cooling_MWh_signed == -loads.iloc[0].cooling_MWh_signed
    control = pd.read_csv(out / "control_summary.csv")
    assert control.free_above_cooling_setpoint_cooling_zero_hours.iloc[0] == 0
    solar = pd.read_csv(out / "solar_summary.csv").set_index("quantity")
    assert solar.loc["total_zone_solar_gain_W", "annual_MWh_or_MWh_m2"] < solar.loc["modelica_total_zone_solar_gain_W", "annual_MWh_or_MWh_m2"]
    attribution = pd.read_csv(out / "attribution_table.csv").set_index("hypothesis")
    assert attribution.loc["annual load integration/sign", "status"] == "REJECTED"
    assert attribution.loc["solar geometry/preprocessing", "status"] == "LIKELY"


def test_three_track_comparison_keeps_diagnostic_out_of_formal_status():
    subprocess.run([sys.executable, "scripts/debug_case600.py"], cwd=ROOT, check=True)
    out = ROOT / "results/case600_debug"
    comparison = pd.read_csv(out / "modelica_solar_comparison.csv").set_index("metric")
    cooling = comparison.loc["annual_cooling_energy"]
    heating = comparison.loc["annual_heating_energy"]
    assert cooling.native_status == "FAIL"
    assert cooling.diagnostic_status == "DIAGNOSTIC_NOT_FORMAL"
    assert cooling.ISO_modelica_solar > 5.0
    assert cooling.change_due_to_solar > 4.0
    assert heating.remaining_difference_to_modelica < 0
    assert (out / "feb1_three_track_load_profile.csv").is_file()
    sensitivity = pd.read_csv(out / "heating_sensitivity_experiments.csv").set_index("experiment")
    assert not bool(sensitivity.loc["air_heat_capacity_1206", "formal_promoted"])
    assert abs(sensitivity.loc["air_heat_capacity_1206", "delta_heating_MWh"]) < 0.01
