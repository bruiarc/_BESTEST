"""Shared 6XX prescribed-delta and report helpers; notebooks contain no model logic."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def prescribed_changes(case: str) -> pd.DataFrame:
    data=json.loads((ROOT/'inputs/case6xx_deltas.json').read_text())
    return pd.DataFrame({'case':case,'prescribed_change':data['cases'][case]['changes'] or ['Base Case 600: no delta']})


def _track(metrics: pd.DataFrame, implementation: str, run_mode: str) -> pd.DataFrame:
    result = metrics[(metrics.implementation == implementation) & (metrics.run_mode == run_mode)].copy()
    if result.empty:
        raise ValueError(f"missing {implementation}/{run_mode} track")
    return result.set_index("metric")


def _value(track: pd.DataFrame, metric: str) -> float:
    return float(track.loc[metric, "value"])


def annual_tracks(metrics: pd.DataFrame) -> pd.DataFrame:
    """Three-track annual results retained in every 6XX notebook."""
    tracks = (
        ("Native ISO", _track(metrics, "iso13790", "native")),
        ("ISO + Modelica solar", _track(metrics, "iso13790", "diagnostic_modelica_solar")),
        ("Modelica native", _track(metrics, "modelica", "native")),
    )
    return pd.DataFrame([
        {"Run": name, "Heating MWh": _value(data, "annual_heating_energy"),
         "Cooling MWh": _value(data, "annual_cooling_energy")}
        for name, data in tracks
    ])


def range_judgement(metrics: pd.DataFrame, reference: pd.DataFrame, case: str) -> pd.DataFrame:
    """Formal native-ISO annual-energy acceptance result, one row per metric."""
    native = _track(metrics, "iso13790", "native")
    rows = []
    for metric, label in (("annual_heating_energy", "Heating"), ("annual_cooling_energy", "Cooling")):
        ref = reference[(reference.case.astype(str) == str(case)) & (reference.metric == metric)].iloc[0]
        value, lower, upper = _value(native, metric), float(ref.lower), float(ref.upper)
        if lower <= value <= upper:
            distance, percent, status = 0.0, 0.0, "PASS"
        elif value < lower:
            distance, percent, status = value - lower, (value - lower) / lower * 100 if lower else float("nan"), "FAIL"
        else:
            distance, percent, status = value - upper, (value - upper) / upper * 100 if upper else float("nan"), "FAIL"
        rows.append({"Metric": label, "Native ISO MWh": value, "ASHRAE lower MWh": lower,
                     "ASHRAE upper MWh": upper, "Distance to violated bound MWh": distance,
                     "Distance %": percent, "Formal status": status})
    return pd.DataFrame(rows)


def peak_tracks(metrics: pd.DataFrame, completed_hour_label) -> pd.DataFrame:
    rows = []
    for label, implementation, run_mode in (
        ("Modelica native", "modelica", "native"), ("Native ISO", "iso13790", "native"),
        ("ISO + Modelica solar", "iso13790", "diagnostic_modelica_solar"),
    ):
        track = _track(metrics, implementation, run_mode)
        heat, cool = track.loc["peak_heating_load"], track.loc["peak_cooling_load"]
        rows.append({"Track": label, "Peak heating kW": float(heat.value),
                     "Peak heating time": completed_hour_label(heat.occurrence_time_s),
                     "Peak cooling kW": float(cool.value),
                     "Peak cooling time": completed_hour_label(cool.occurrence_time_s)})
    return pd.DataFrame(rows)


def comparison_table(metrics: pd.DataFrame, comparison: str) -> pd.DataFrame:
    """Controlled residual or native-to-controlled solar effect for four metrics."""
    modelica = _track(metrics, "modelica", "native")
    native = _track(metrics, "iso13790", "native")
    controlled = _track(metrics, "iso13790", "diagnostic_modelica_solar")
    rows = []
    for metric, label, unit in (
        ("annual_heating_energy", "Annual heating", "MWh"),
        ("annual_cooling_energy", "Annual cooling", "MWh"),
        ("peak_heating_load", "Peak heating", "kW"),
        ("peak_cooling_load", "Peak cooling", "kW"),
    ):
        if comparison == "controlled_modelica":
            base, other, base_label, other_label = _value(modelica, metric), _value(controlled, metric), "Modelica", "ISO + Modelica solar"
        elif comparison == "solar_effect":
            base, other, base_label, other_label = _value(native, metric), _value(controlled, metric), "Native ISO", "ISO + Modelica solar"
        else:
            raise ValueError(comparison)
        difference = other - base
        rows.append({"Metric": label, "Unit": unit, base_label: base, other_label: other,
                     "Difference": difference, "Difference %": difference / base * 100 if base else float("nan")})
    return pd.DataFrame(rows)
