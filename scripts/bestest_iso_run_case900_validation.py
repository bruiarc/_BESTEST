#!/usr/bin/env python3
"""Case 900 wrapper using the established Modelica/RClib BESTEST pipeline."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODELICA_ROOT = ROOT / "0_modelica"
MODELICA_RESULTS = ROOT.parent / "_modelica" / "results"
sys.path.insert(0, str(MODELICA_ROOT))
from iso_validation.bestest_pipeline import CASE_DEFINITIONS, annual_metrics, modelica_track, published_reference_tables, run_rclib_matched_forcing, run_rclib_native_solar
from iso_validation.modelica_runner import run_validation_model

CASE = "900"
COLS = ["timestamp_s", "case", "implementation", "run_mode", "formal_ashrae_result", "zone_temperature_C", "heating_load_W", "cooling_load_W", "outdoor_temperature_C", "solar_gain_W"]

def standard(frame, implementation, run_mode, solar):
    return pd.DataFrame({"timestamp_s": frame.time_s, "case": CASE, "implementation": implementation, "run_mode": run_mode, "formal_ashrae_result": run_mode == "native", "zone_temperature_C": frame["modelica_air_temperature_c"] if implementation == "modelica" else frame["rclib_air_temperature_c"], "heating_load_W": frame["modelica_heating_w"] if implementation == "modelica" else frame["rclib_heating_w"], "cooling_load_W": frame["modelica_cooling_w"] if implementation == "modelica" else frame["rclib_cooling_w"], "outdoor_temperature_C": frame.outdoor_temperature_c, "solar_gain_W": frame[solar]})[COLS]

def metrics(frame, implementation, run_mode):
    source = "Modelica" if implementation == "modelica" else "RClib"
    metric_frame = pd.DataFrame({"time_s": frame.timestamp_s, "modelica_heating_w": frame.heating_load_W, "modelica_cooling_w": frame.cooling_load_W, "rclib_heating_w": frame.heating_load_W, "rclib_cooling_w": frame.cooling_load_W})
    out = annual_metrics(metric_frame, CASE_DEFINITIONS[CASE], source=source)
    return out.assign(implementation=implementation, run_mode=run_mode, formal_ashrae_result=run_mode == "native")

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--run-modelica", action="store_true"); parser.add_argument("--output", type=Path, default=ROOT / "results/1_iso/case900"); args = parser.parse_args(); out=args.output; out.mkdir(parents=True, exist_ok=True)
    raw_path = MODELICA_RESULTS / "Case900/Case900_res.csv"
    if raw_path.is_file(): raw = pd.read_csv(raw_path)
    elif args.run_modelica: raw, _, _ = run_validation_model(CASE_DEFINITIONS[CASE].modelica_class)
    else: raise FileNotFoundError(f"No cached Case900 result: {raw_path}")
    modelica = modelica_track(raw); modelica_std = standard(modelica, "modelica", "native", "modelica_resolved_solar_gain_w")
    modelica_std.to_csv(MODELICA_RESULTS / "Case900/Case900_standardized_hourly.csv", index=False)
    native = run_rclib_native_solar(CASE_DEFINITIONS[CASE], raw); native_std = standard(native, "iso13790", "native", "native_rclib_solar_gain_w"); native_std.to_csv(out / "case900_iso13790_native_hourly.csv", index=False)
    diagnostic = run_rclib_matched_forcing(CASE_DEFINITIONS[CASE], raw); diagnostic_std = standard(diagnostic, "iso13790", "diagnostic_modelica_solar", "modelica_resolved_solar_gain_w"); diagnostic_std.to_csv(out / "case900_iso13790_diagnostic_modelica_solar_hourly.csv", index=False)
    all_metrics = pd.concat([metrics(modelica_std,"modelica","native"), metrics(native_std,"iso13790","native"), metrics(diagnostic_std,"iso13790","diagnostic_modelica_solar")], ignore_index=True); all_metrics.to_csv(out / "case900_metrics.csv",index=False)
    refs=published_reference_tables(); refs=refs[(refs.case==CASE)&refs.metric.isin(["annual_heating_energy","annual_cooling_energy"])]
    formal=all_metrics[all_metrics.run_mode.eq("native") & all_metrics.metric.isin(refs.metric)].merge(refs[["case","metric","lower","upper"]],on=["case","metric"]); formal["within_ashrae_range"]=formal.value.between(formal.lower,formal.upper); formal.to_csv(out / "case900_formal_ashrae_energy.csv",index=False)
    feb_start,feb_end=31*86400+3600,32*86400; pd.concat([modelica_std,native_std,diagnostic_std]).query("@feb_start <= timestamp_s <= @feb_end").to_csv(out / "case900_feb1_load_profile.csv",index=False)
    solar=pd.DataFrame([{"quantity":"native_rclib_zone_solar_MWh", "value":native_std.solar_gain_W.sum()/1e6},{"quantity":"modelica_resolved_zone_solar_MWh", "value":modelica_std.solar_gain_W.sum()/1e6}]); solar.loc[2]=["difference_MWh",solar.value.iloc[1]-solar.value.iloc[0]]; solar.loc[3]=["difference_percent_of_modelica",100*(solar.value.iloc[1]-solar.value.iloc[0])/solar.value.iloc[1]]; solar.to_csv(out / "case900_solar_comparison.csv",index=False)
    piv=all_metrics.pivot_table(index="metric",columns=["implementation","run_mode"],values="value"); rows=[]
    for m in piv.index: rows.append({"metric":m,"iso_modelica_solar":piv.loc[m,("iso13790","diagnostic_modelica_solar")],"modelica_native":piv.loc[m,("modelica","native")],"difference":piv.loc[m,("iso13790","diagnostic_modelica_solar")]-piv.loc[m,("modelica","native")]})
    pd.DataFrame(rows).to_csv(out / "case900_controlled_forcing_comparison.csv",index=False)
    pd.DataFrame({"required_file":["case900_iso13790_native_hourly.csv","case900_iso13790_diagnostic_modelica_solar_hourly.csv","case900_metrics.csv","case900_formal_ashrae_energy.csv","case900_feb1_load_profile.csv","case900_solar_comparison.csv","case900_controlled_forcing_comparison.csv"]}).to_csv(out / "manifest.csv",index=False)
if __name__ == "__main__": main()
