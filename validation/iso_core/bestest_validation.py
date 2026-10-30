"""Minimal Case 600FF comparison used by the ISO validation runner."""
from pathlib import Path

import numpy as np
import pandas as pd

from .dependencies import zone_class


def run_case600ff(modelica_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compare RClib Case 600FF against Modelica's hourly forcing."""
    raw = pd.read_csv(modelica_csv)
    times = np.arange(3600, 31536001, 3600)

    def values(column: str):
        return np.interp(times, raw.time, raw[column].astype(float))

    opaque_area = 159.6
    total_area = 171.6
    zone = zone_class()(
        window_area=12.0,
        walls_area=opaque_area,
        floor_area=48.0,
        room_vol=129.6,
        total_internal_area=total_area,
        u_windows=3.1,
        u_walls=(0.534 * 63.6 + 0.327 * 48.0 + 0.0377 * 48.0) / opaque_area,
        ach_vent=0.414,
        ach_infl=0.0,
        ventilation_efficiency=0.0,
        thermal_capacitance_per_floor_area=42167.0,
        effective_mass_area_per_floor_area=2.95,
        t_set_heating=-1e6,
        t_set_cooling=1e6,
    )
    zone.h_tr_is = 3.45 * total_area
    zone.h_ve_adj = 1200.0 * 0.414 * 129.6 / 3600.0
    mass = air = 20.0
    temperatures = []
    for solar, outdoor in zip(
        values("zonHVAC.solGai.y"), values("weaDat.weaBus.TDryBul") - 273.15
    ):
        zone.solve_energy(200.0, float(solar), float(outdoor), mass, air,
                          heating_available=False)
        mass, air = zone.t_m_next, zone.t_air
        temperatures.append(air)

    aligned = pd.DataFrame({
        "time": times,
        "ethlib_tair_c": temperatures,
        "modelica_tair_c": values("zonHVAC.TAir") - 273.15,
        "outdoor_temperature_c": values("weaDat.weaBus.TDryBul") - 273.15,
        "modelica_solar_gain_w": values("zonHVAC.solGai.y"),
    })
    aligned["ethlib_minus_modelica_c"] = aligned.ethlib_tair_c - aligned.modelica_tair_c
    residual = aligned.ethlib_minus_modelica_c
    metrics = pd.DataFrame([{
        "Case": "600FF",
        "Compared variable": "ETHlib T_air − Modelica TAir",
        "Rows": len(aligned),
        "MAE °C": residual.abs().mean(),
        "RMSE °C": np.sqrt((residual * residual).mean()),
        "Max abs. °C": residual.abs().max(),
    }])
    diagnostics = pd.DataFrame([
        ("geometry and envelope", "48 m2 / 129.6 m3; conserve sum(UA)", True),
        ("thermal mass", "42167 J/(m2 K), factor 2.95", True),
        ("solar radiation", "Modelica solGai secondary comparison", False),
    ], columns=["Modelica source quantity", "mapping", "exact"])
    return aligned, metrics, diagnostics
