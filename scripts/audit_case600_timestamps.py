#!/usr/bin/env python3
"""Audit Case 600 Modelica/ISO completed-hour labels without shifting values."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODELICA_RAW = ROOT.parent / "_modelica" / "results" / "Case600" / "Case600_res.csv"
ISO_RUN_MODES = {"modelica_solar": "diagnostic_modelica_solar", "native": "native"}


def _interval_label(end_seconds: float) -> str:
    end = pd.Timestamp("1995-01-01") + pd.to_timedelta(end_seconds, unit="s")
    start = end - pd.Timedelta(hours=1)
    return f"{start:%d-%b %H:%M}–{end:%H:%M}"


def build_audit(iso_mode: str) -> pd.DataFrame:
    try:
        iso_run_mode = ISO_RUN_MODES[iso_mode]
    except KeyError as exc:
        raise ValueError(f"iso_mode must be one of {tuple(ISO_RUN_MODES)}") from exc
    raw = pd.read_csv(MODELICA_RAW)
    profile = pd.read_csv(ROOT / "results" / "case600" / "case600_feb1_load_profile.csv")
    modelica = profile[(profile.implementation == "modelica") & (profile.run_mode == "native")].copy()
    iso = profile[(profile.implementation == "iso13790") & (profile.run_mode == iso_run_mode)].copy()
    if len(modelica) != 24 or len(iso) != 24:
        raise ValueError("Case 600 February profile must contain 24 rows per selected track")
    modelica = modelica.sort_values("timestamp_s").reset_index(drop=True)
    iso = iso.sort_values("timestamp_s").reset_index(drop=True)
    # `PHea.y` and `PCoo.y` are Modelica MovingAverage(delta=3600) signals;
    # direct interpolation at the report endpoint is intentional.
    t = modelica.timestamp_s.to_numpy()
    check_heat = np.interp(t, raw.time, raw["PHea.y"])
    check_cool = -np.interp(t, raw.time, raw["PCoo.y"])
    if not np.allclose(check_heat, modelica.heating_load_W) or not np.allclose(check_cool, modelica.cooling_load_W):
        raise ValueError("standardized Modelica profile is not the raw endpoint extraction")
    hours = ((t / 3600 - 1) % 24 + 1).astype(int)
    if not np.array_equal(hours, np.arange(1, 25)) or not np.array_equal(iso.timestamp_s.to_numpy(), t):
        raise ValueError("Modelica and ISO February profiles do not share the completed-hour grid")
    return pd.DataFrame({
        "physical_interval": [_interval_label(value) for value in t],
        "modelica_raw_timestamp": t,
        "modelica_completed_hour": hours,
        "iso_raw_timestamp": iso.timestamp_s.to_numpy(),
        "iso_completed_hour": hours,
        "modelica_heating_W": modelica.heating_load_W.to_numpy(),
        "iso_heating_W": iso.heating_load_W.to_numpy(),
        "modelica_cooling_W": modelica.cooling_load_W.to_numpy(),
        "iso_cooling_W": iso.cooling_load_W.to_numpy(),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso-mode", default="modelica_solar", choices=ISO_RUN_MODES)
    args = parser.parse_args()
    output = ROOT / "results" / "case600" / f"case600_feb1_timestamp_alignment_{args.iso_mode}.csv"
    build_audit(args.iso_mode).to_csv(output, index=False)


if __name__ == "__main__":
    main()
