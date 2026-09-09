#!/usr/bin/env python3
"""Parameterised 9XX runner using the established Modelica/RClib pipeline."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / "modelica_test_2"
MODEL = ROOT.parent / "_modelica" / "results"
sys.path.insert(0, str(LEGACY))
sys.path.insert(0, str(ROOT / "scripts"))
from iso_validation.bestest_pipeline import CASE_DEFINITIONS, annual_metrics, modelica_track, published_reference_tables, run_rclib_matched_forcing, run_rclib_native_solar
from iso_validation.modelica_runner import run_validation_model
from run_case6xx import standard, metric

CASES = ("910", "920", "930", "940", "950", "980", "985", "995")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES)
    parser.add_argument("--run-modelica", action="store_true")
    args = parser.parse_args(); case = args.case
    raw_path = MODEL / f"Case{case}" / f"Case{case}_res.csv"
    if raw_path.is_file(): raw = pd.read_csv(raw_path)
    elif args.run_modelica: raw, _, _ = run_validation_model(CASE_DEFINITIONS[case].modelica_class)
    else: raise FileNotFoundError(f"Missing {raw_path}; rerun with --run-modelica")
    out = ROOT / "results" / f"case{case}"; out.mkdir(parents=True, exist_ok=True)
    modelica = standard(modelica_track(raw), case, "modelica", "native", "modelica_resolved_solar_gain_w")
    (MODEL / f"Case{case}").mkdir(parents=True, exist_ok=True)
    modelica.to_csv(MODEL / f"Case{case}" / f"Case{case}_standardized_hourly.csv", index=False)
    native = standard(run_rclib_native_solar(CASE_DEFINITIONS[case], raw), case, "iso13790", "native", "native_rclib_solar_gain_w")
    diagnostic = standard(run_rclib_matched_forcing(CASE_DEFINITIONS[case], raw), case, "iso13790", "diagnostic_modelica_solar", "modelica_resolved_solar_gain_w")
    native.to_csv(out / f"case{case}_iso13790_native_hourly.csv", index=False)
    diagnostic.to_csv(out / f"case{case}_iso13790_diagnostic_modelica_solar_hourly.csv", index=False)
    metrics = pd.concat([metric(modelica, case, "modelica", "native"), metric(native, case, "iso13790", "native"), metric(diagnostic, case, "iso13790", "diagnostic_modelica_solar")])
    metrics.to_csv(out / f"case{case}_metrics.csv", index=False)
    refs = published_reference_tables(); refs = refs[(refs.case == case) & refs.metric.isin(["annual_heating_energy", "annual_cooling_energy"])]
    formal = metrics[metrics.run_mode.eq("native") & metrics.metric.isin(refs.metric)].merge(refs[["case", "metric", "lower", "upper"]], on=["case", "metric"])
    formal["within_ashrae_range"] = formal.value.between(formal.lower, formal.upper)
    formal.to_csv(out / f"case{case}_formal_ashrae_energy.csv", index=False)
    solar = pd.DataFrame({"quantity": ["native_rclib_zone_solar_MWh", "modelica_resolved_zone_solar_MWh"], "value": [native.solar_gain_W.sum()/1e6, modelica.solar_gain_W.sum()/1e6]})
    solar.loc[2] = ["native_modelica_ratio", solar.value.iloc[0] / solar.value.iloc[1]]
    solar.to_csv(out / f"case{case}_solar_comparison.csv", index=False)

if __name__ == "__main__": main()
