"""Small, data-first helpers for the LBNL-style BESTEST report notebooks.

The helpers consume standardized result files.  They deliberately contain no
simulation, debugging, or pass/fail policy beyond numeric annual-energy bounds
published in the reporting reference.
"""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


ISO_MODES = {
    "modelica_solar": ("diagnostic_modelica_solar", "Python ISO 13790 + Modelica-resolved solar"),
    "native": ("native", "Python ISO 13790 native solar"),
}
MODELICA_LABEL = "Modelica native"


def selected_iso_mode(mode: str) -> tuple[str, str]:
    """Return standardized run-mode and display label for a report switch."""
    try:
        return ISO_MODES[mode]
    except KeyError as exc:
        raise ValueError(f"ISO_MODE must be one of {tuple(ISO_MODES)}; got {mode!r}") from exc


def markdown_table(reference: Path, section: str) -> pd.DataFrame:
    """Parse one reference Markdown table without duplicating its values."""
    lines = reference.read_text().splitlines()
    try:
        # Sections are numbered in the reference (`# 3. ...`); accept that
        # stable suffix without encoding reference numbers in report code.
        start = next(i for i, line in enumerate(lines) if line.startswith("# ") and line.endswith(section))
    except StopIteration as exc:
        raise ValueError(f"section not found: {section}") from exc
    table = []
    for line in lines[start + 1:]:
        if line.startswith("# "):
            break
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not all(set(cell) <= {"-", ":"} for cell in cells):
                table.append(cells)
    if not table:
        raise ValueError(f"no Markdown table in: {section}")
    return pd.DataFrame(table[1:], columns=table[0])


def reference_for_case(reference: Path, section: str, case: str) -> pd.Series:
    frame = markdown_table(reference, section)
    result = frame.loc[frame.Case.astype(str) == str(case)]
    if len(result) != 1:
        raise ValueError(f"expected one {case} row in {section}; found {len(result)}")
    return result.iloc[0]


def completed_hour_label(seconds: float | int | None) -> str:
    """Return LBNL-compatible day/month/hour notation for a non-leap year."""
    if pd.isna(seconds):
        return ""
    index = pd.Timestamp("1995-01-01") + pd.to_timedelta(float(seconds), unit="s")
    return f"{index.day:02d}-{index.strftime('%b')}:{index.hour:02d}"


def selected_metrics(metrics: pd.DataFrame, iso_mode: str) -> pd.DataFrame:
    """Keep exactly Modelica native and the selected ISO reporting scenario."""
    iso_run_mode, iso_label = selected_iso_mode(iso_mode)
    modelica = metrics[(metrics.implementation == "modelica") & (metrics.run_mode == "native")].copy()
    modelica["display_run"] = MODELICA_LABEL
    iso = metrics[(metrics.implementation == "iso13790") & (metrics.run_mode == iso_run_mode)].copy()
    iso["display_run"] = iso_label
    if modelica.empty or iso.empty:
        raise ValueError(f"missing Modelica native or ISO {iso_mode!r} metric track")
    return pd.concat((modelica, iso), ignore_index=True)


def annual_energy_table(metrics: pd.DataFrame, reference: Path, case: str, metric: str, iso_mode: str) -> pd.DataFrame:
    """LBNL-style annual table: reference programs, bounds, two computed runs."""
    section = "Annual heating energy reference data" if metric == "annual_heating_energy" else "Annual cooling energy reference data"
    ref = reference_for_case(reference, section, case)
    selected = selected_metrics(metrics, iso_mode).set_index("metric")
    row = {"Case": str(case), "ASHRAE lower": float(ref["Lower"]), "ASHRAE upper": float(ref["Upper"])}
    for program in ("BSIMAC", "CSE", "DeST", "EnergyPlus", "ESP-r", "TRNSYS"):
        row[program] = float(ref[program])
    row[MODELICA_LABEL] = float(selected.loc[metric].loc[lambda x: x.display_run == MODELICA_LABEL, "value"].iloc[0])
    iso_run_mode, iso_label = selected_iso_mode(iso_mode)
    iso_value = float(selected.loc[metric].loc[lambda x: x.display_run == iso_label, "value"].iloc[0])
    row[iso_label] = iso_value
    within_range = row["ASHRAE lower"] <= iso_value <= row["ASHRAE upper"]
    status = "PASS" if within_range else "FAIL"
    # Controlled forcing is assessed against the same published numbers for
    # comparison, while the suffix prevents it being mistaken for formal native
    # ASHRAE validation.
    row["Python range status"] = f"{status} — diagnostic" if iso_mode != "native" else status
    return pd.DataFrame([row])


def peak_table(metrics: pd.DataFrame, reference: Path, case: str, metric: str, iso_mode: str) -> pd.DataFrame:
    section = "Peak heating reference data" if metric == "peak_heating_load" else "Peak cooling reference data"
    ref = reference_for_case(reference, section, case)
    selected = selected_metrics(metrics, iso_mode)
    selected = selected[selected.metric == metric].copy()
    row = {"Case": str(case)}
    for program in ("BSIMAC", "CSE", "DeST", "EnergyPlus", "ESP-r", "TRNSYS"):
        row[program] = f"{ref[program]} ({ref[f'{program} hour']})"
    for run in (MODELICA_LABEL, selected_iso_mode(iso_mode)[1]):
        item = selected[selected.display_run == run].iloc[0]
        row[run] = f"{item.value:.3f} ({completed_hour_label(item.occurrence_time_s)})"
    return pd.DataFrame([row])


def selected_hourly(hourly: pd.DataFrame, iso_mode: str) -> pd.DataFrame:
    iso_run_mode, _ = selected_iso_mode(iso_mode)
    return hourly[((hourly.implementation == "modelica") & (hourly.run_mode == "native")) |
                  ((hourly.implementation == "iso13790") & (hourly.run_mode == iso_run_mode))].copy()


def daily_slice(hourly: pd.DataFrame, month: int, day: int) -> pd.DataFrame:
    """Slice completed-hour data, assigning each interval to its ending day.

    The 24:00 result for 1 February is stored at 2 February 00:00. Subtracting
    one second only for calendar labelling keeps that completed interval in the
    LBNL-reported 1 February profile without changing any model result.
    """
    interval_day = pd.Timestamp("1995-01-01") + pd.to_timedelta(hourly.timestamp_s - 1, unit="s")
    mask = (interval_day.dt.month == month) & (interval_day.dt.day == day)
    completed_hour = ((hourly.loc[mask, "timestamp_s"] / 3600 - 1) % 24 + 1).astype(int)
    return hourly.loc[mask].assign(hour=completed_hour)
