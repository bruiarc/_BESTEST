#!/usr/bin/env python3
"""Case 600 ASHRAE 140 pilot; wraps existing Modelica/RClib workflows."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODELICA_ROOT = ROOT / "0_modelica"
MODELICA_RESULTS = ROOT.parent / "_modelica" / "results"
sys.path.insert(0, str(MODELICA_ROOT))

from iso_validation.bestest_pipeline import (  # noqa: E402
    CASE_DEFINITIONS, annual_metrics, modelica_track, published_reference_tables,
    run_rclib_matched_forcing, run_rclib_native_solar,
)
from iso_validation.modelica_runner import run_validation_model  # noqa: E402
from iso_validation.bestest_validation import run_case600ff  # noqa: E402

CASE = "600"
STANDARD_COLUMNS = ["timestamp_s", "case", "implementation", "run_mode", "formal_ashrae_result", "zone_temperature_C", "heating_load_W", "cooling_load_W", "outdoor_temperature_C", "solar_gain_W"]


def _raw_modelica(run_missing: bool) -> pd.DataFrame:
    cached = MODELICA_RESULTS / "Case600" / "Case600_res.csv"
    if cached.is_file():
        return pd.read_csv(cached)
    if not run_missing:
        raise FileNotFoundError(f"No cached Case600 result: {cached}; re-run with --run-modelica")
    frame, _, _ = run_validation_model(CASE_DEFINITIONS[CASE].modelica_class)
    return frame


def _standardize(frame: pd.DataFrame, *, implementation: str, run_mode: str, formal: bool, solar: str) -> pd.DataFrame:
    return pd.DataFrame({
        "timestamp_s": frame.time_s, "case": CASE, "implementation": implementation,
        "run_mode": run_mode, "formal_ashrae_result": formal,
        "zone_temperature_C": frame["modelica_air_temperature_c"] if implementation == "modelica" else frame["rclib_air_temperature_c"],
        "heating_load_W": frame["modelica_heating_w"] if implementation == "modelica" else frame["rclib_heating_w"],
        "cooling_load_W": frame["modelica_cooling_w"] if implementation == "modelica" else frame["rclib_cooling_w"],
        "outdoor_temperature_C": frame.outdoor_temperature_c,
        "solar_gain_W": frame[solar],
    })[STANDARD_COLUMNS]


def _metrics(standard: pd.DataFrame, raw_frame: pd.DataFrame, implementation: str, run_mode: str) -> pd.DataFrame:
    """Use the same explicit hourly integration/peak rules for all outputs."""
    source_frame = pd.DataFrame({"time_s": standard.timestamp_s, "modelica_heating_w": standard.heating_load_W,
        "modelica_cooling_w": standard.cooling_load_W, "rclib_heating_w": standard.heating_load_W,
        "rclib_cooling_w": standard.cooling_load_W})
    source = "Modelica" if implementation == "modelica" else "RClib"
    metrics = annual_metrics(source_frame, CASE_DEFINITIONS[CASE], source=source)
    metrics["implementation"] = implementation; metrics["run_mode"] = run_mode
    metrics["formal_ashrae_result"] = run_mode == "native"
    return metrics


def _formal_table(metrics: pd.DataFrame) -> pd.DataFrame:
    refs = published_reference_tables()
    refs = refs[(refs.case == CASE) & refs.metric.isin(["annual_heating_energy", "annual_cooling_energy"])]
    native = metrics[metrics.run_mode.eq("native") & metrics.metric.isin(refs.metric)].copy()
    out = native.merge(refs[["case", "metric", "lower", "upper"]], on=["case", "metric"], how="left")
    out["within_ashrae_range"] = out.value.between(out.lower, out.upper)
    return out


def _case600ff_regression(out: Path) -> pd.DataFrame:
    """Wrap the established diagnostic path without making it a formal test."""
    source = MODELICA_RESULTS / "Case600FF" / "Case600FF_res.csv"
    aligned, metrics, _ = run_case600ff(source)
    standard = pd.DataFrame({
        "timestamp_s": aligned.time, "case": "600FF", "implementation": "iso13790",
        "run_mode": "diagnostic_modelica_solar", "formal_ashrae_result": False,
        "zone_temperature_C": aligned.ethlib_tair_c, "heating_load_W": 0.0,
        "cooling_load_W": 0.0, "outdoor_temperature_C": aligned.outdoor_temperature_c,
        "solar_gain_W": aligned.modelica_solar_gain_w,
    })[STANDARD_COLUMNS]
    standard.to_csv(out / "case600ff_iso13790_diagnostic_modelica_solar_hourly.csv", index=False)
    summary = metrics.rename(columns={"MAE °C": "mae_C", "RMSE °C": "rmse_C", "Max abs. °C": "max_abs_C"})
    summary["formal_ashrae_result"] = False
    summary.to_csv(out / "case600ff_regression_summary.csv", index=False)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-modelica", action="store_true", help="run existing Modelica wrapper if Case600 cache is absent")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "1_iso" / "case600")
    args = parser.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=True)

    raw = _raw_modelica(args.run_modelica)
    modelica = modelica_track(raw)
    modelica_std = _standardize(modelica, implementation="modelica", run_mode="native", formal=True, solar="modelica_resolved_solar_gain_w")
    modelica_archive = MODELICA_RESULTS / "Case600"
    modelica_archive.mkdir(parents=True, exist_ok=True)
    modelica_std.to_csv(modelica_archive / "Case600_standardized_hourly.csv", index=False)

    # Formal ISO run: RClib reads the Denver EPW and calculates solar itself.
    iso_native = run_rclib_native_solar(CASE_DEFINITIONS[CASE], raw)
    iso_native_std = _standardize(iso_native, implementation="iso13790", run_mode="native", formal=True, solar="native_rclib_solar_gain_w")
    iso_native_std.to_csv(out / "case600_iso13790_native_hourly.csv", index=False)

    # Diagnostic only: this receives Modelica's already-resolved net zone gain.
    iso_diagnostic = run_rclib_matched_forcing(CASE_DEFINITIONS[CASE], raw)
    iso_diagnostic_std = _standardize(iso_diagnostic, implementation="iso13790", run_mode="diagnostic_modelica_solar", formal=False, solar="modelica_resolved_solar_gain_w")
    iso_diagnostic_std.to_csv(out / "case600_iso13790_diagnostic_modelica_solar_hourly.csv", index=False)

    all_metrics = pd.concat([
        _metrics(modelica_std, modelica, "modelica", "native"),
        _metrics(iso_native_std, iso_native, "iso13790", "native"),
        _metrics(iso_diagnostic_std, iso_diagnostic, "iso13790", "diagnostic_modelica_solar"),
    ], ignore_index=True)
    all_metrics.to_csv(out / "case600_metrics.csv", index=False)
    _formal_table(all_metrics).to_csv(out / "case600_formal_ashrae_energy.csv", index=False)
    feb_start, feb_end = 31 * 86400 + 3600, 32 * 86400
    pd.concat([modelica_std, iso_native_std, iso_diagnostic_std], ignore_index=True).query(
        "@feb_start <= timestamp_s <= @feb_end"
    ).to_csv(out / "case600_feb1_load_profile.csv", index=False)
    _case600ff_regression(out)

    pd.DataFrame({"required_file": ["case600_iso13790_native_hourly.csv", "case600_iso13790_diagnostic_modelica_solar_hourly.csv", "case600_metrics.csv", "case600_formal_ashrae_energy.csv", "case600_feb1_load_profile.csv", "case600ff_iso13790_diagnostic_modelica_solar_hourly.csv", "case600ff_regression_summary.csv"]}).to_csv(out / "manifest.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
