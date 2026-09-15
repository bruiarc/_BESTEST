"""Controlled Case 600 VDI–Modelica crosswalk used by the single study notebook."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
BESTEST = HERE.parent
DEV = HERE.parents[2]
sys.path.insert(0, str(DEV / "RC_br"))

from RClib.vdi6007 import RCCase, run_thermostat_case
from RClib.vdi6007.case_adapter import VDIAdapterDefaults
from RClib.vdi6007.no_iw import run_thermostat_case_no_iw
from RClib.vdi6007.types import (
    ExteriorRadiantAllocation, ExteriorRadiantSource, ExteriorSourceContribution,
    InternalRadiantAllocation,
)
import RClib.vdi6007.orchestration as orchestration
import RClib.vdi6007.no_iw as no_iw

AREA, VOLUME, RHO, CP = 48.0, 129.6, 1.20, 1005.0
INDEX = pd.date_range("2023-01-01", periods=8760, freq="h")
ONES, ZEROS = np.ones(8760), np.zeros(8760)
WEATHER = DEV / "2_validation/modelica_test_2/modelica-buildings-github-master/Buildings/Resources/weatherdata/USA_CO_Denver.Intl.AP.725650_TMY3.epw"
SOLAR_FILE = BESTEST / "results/case600/case600_iso13790_diagnostic_modelica_solar_hourly.csv"
OUT = HERE / "results/case600_vdi_crosswalk"

# ISO/Modelica Zone5R1C source fractions, evaluated from the checked-in Case 600 inputs.
AT, AM, HTRW, HSUR = 171.6, 141.6, 37.2, 9.1
ISO_F_IW = AM / AT
ISO_F_AIR = HTRW / (HSUR * AT)
ISO_F_AW = 1.0 - ISO_F_IW - ISO_F_AIR


@dataclass(frozen=True)
class Scenario:
    name: str
    interpretation: str
    topology: str = "IW"
    solar_air: float = 0.0
    solar_aw: float | None = None
    internal_air: float = 1.0
    internal_aw: float | None = None
    construction_mode: str = "layer-controlled"
    inside_h: float = 8.0
    neutral_longwave: bool = False
    ach: float = 0.414
    solar_group: str = "modelica"


def modelica_solar() -> np.ndarray:
    frame = pd.read_csv(SOLAR_FILE)
    assert len(frame) == 8760
    assert np.array_equal(frame.timestamp_s.to_numpy(), np.arange(1, 8761) * 3600.0)
    solar = frame.solar_gain_W.to_numpy(float)
    # This is a signed Modelica-resolved net solar object (its night value
    # includes the comparator's window-radiation correction), so preserve it.
    assert np.isfinite(solar).all()
    return solar


def _case(s: Scenario) -> RCCase:
    defaults = VDIAdapterDefaults(
        inside_total_coefficient_w_m2k=s.inside_h,
        heating_convective_fraction=1.0,
        cooling_convective_fraction=1.0,
        internal_gain_convective_fraction=s.internal_air,
    )
    return RCCase(
        year=2023, loc_json=HERE / "inputs/case600_location.json",
        geo_json=HERE / "inputs/case600_geometry.json",
        default_json=HERE / "inputs/case600_defaults.json", epw_path=WEATHER,
        occupancy_profile_csv=HERE / "inputs/case600_occupancy.csv",
        adapter_defaults=defaults,
        use_construction_properties=s.construction_mode == "layer-controlled",
    )


def _neutralize_longwave(boundary):
    # Setting both long-wave fields to the reference black-body radiation at
    # outdoor dry bulb makes the VDI equivalent long-wave temperature offset zero.
    t_k = boundary.radiation.outdoor_air_temperature_c + 273.15
    lw = 0.93 * 5.670374419e-8 * t_k**4
    rad = replace(boundary.radiation, atmospheric_radiation_w_m2=lw,
                  ground_radiation_w_m2=lw)
    return replace(boundary, radiation=rad)


def _transform(s: Scenario, solar: np.ndarray, applied_solar: list[float] | None = None):
    resistance = 1.0 / (RHO * CP * s.ach * VOLUME / 3600.0)
    def apply(position, hourly):
        sw = float(solar[position])
        if applied_solar is not None and s.solar_group == "modelica":
            applied_solar.append(sw)
        if s.solar_group == "native_vdi":
            boundaries = hourly.boundary_inputs
            if s.neutral_longwave:
                boundaries = tuple(_neutralize_longwave(b) for b in boundaries)
            sources = hourly.exterior_radiant_sources
            convective = hourly.internal_convective_gain_w
            native_total = sum(x.radiant_source_w for x in sources)
            if applied_solar is not None:
                applied_solar.append(native_total)
            if s.solar_aw is not None:
                convective += s.solar_air*native_total
                sources = tuple(replace(x, radiant_source_w=(1.0-s.solar_air)*x.radiant_source_w)
                                for x in sources)
            return replace(hourly, boundary_inputs=boundaries,
                           exterior_radiant_sources=sources,
                           internal_convective_gain_w=convective,
                           ventilation_resistance_k_w=resistance)
        if s.solar_group != "modelica":
            raise ValueError(f"unknown solar_group {s.solar_group!r}")
        boundaries = tuple(replace(b, direct_surface_irradiance_w_m2=0.0,
                                   diffuse_surface_irradiance_w_m2=0.0)
                           for b in hourly.boundary_inputs)
        if s.neutral_longwave:
            boundaries = tuple(_neutralize_longwave(b) for b in boundaries)
        # Modelica solar is the sole solar object: native opaque and window paths
        # are disabled, then the one series is split only at the selected nodes.
        return replace(
            hourly, boundary_inputs=boundaries,
            ventilation_resistance_k_w=resistance,
            internal_convective_gain_w=hourly.internal_convective_gain_w + s.solar_air * sw,
            internal_radiant_gain_w=hourly.internal_radiant_gain_w,
            exterior_radiant_sources=(ExteriorRadiantSource(
                "unified Modelica solar", (1.0-s.solar_air)*sw, 0.0, "aggregate"
            ),),
        )
    return apply


@contextmanager
def _source_crosswalk(s: Scenario):
    original_o = orchestration.allocate_internal_radiant_source
    original_n = no_iw.allocate_internal_radiant_source
    original_oe = orchestration.allocate_exterior_radiant_sources
    original_ne = no_iw.allocate_exterior_radiant_sources

    def allocate(*, total_internal_radiant_source_w, room_surface_area_m2, aw_surface_area_m2):
        total = float(total_internal_radiant_source_w)
        default_aw = aw_surface_area_m2 / room_surface_area_m2
        internal_aw = default_aw if s.internal_aw is None else s.internal_aw / (1.0-s.internal_air)
        if s.internal_air == 1: internal_aw = 0.0
        aw = total * internal_aw
        iw = total - aw
        aw_fraction = 0.0 if total == 0 else aw / total
        return InternalRadiantAllocation(iw_source_w=iw, aw_source_w=aw,
            iw_fraction=1.0-aw_fraction, aw_fraction=aw_fraction, total_source_w=total)

    def allocate_solar(*, sources, room_surface_area_m2, aw_surface_area_m2):
        source_items = tuple(sources)
        if s.solar_group == "native_vdi" and s.solar_aw is None:
            return original_oe(sources=source_items,
                room_surface_area_m2=room_surface_area_m2,
                aw_surface_area_m2=aw_surface_area_m2)
        total = sum(source.radiant_source_w for source in source_items)
        default_aw = aw_surface_area_m2 / room_surface_area_m2
        aw_fraction = default_aw if s.solar_aw is None else s.solar_aw / (1.0-s.solar_air)
        if s.solar_air == 1: aw_fraction = 0.0
        aw, iw = total*aw_fraction, total*(1.0-aw_fraction)
        items = tuple(ExteriorSourceContribution(
            source.name, source.radiant_source_w, 1.0-aw_fraction, aw_fraction,
            source.radiant_source_w*(1.0-aw_fraction),
            source.radiant_source_w*aw_fraction, 0.0, source.orientation_id)
            for source in source_items)
        return ExteriorRadiantAllocation(iw, aw, total, items)

    orchestration.allocate_internal_radiant_source = allocate
    no_iw.allocate_internal_radiant_source = allocate
    orchestration.allocate_exterior_radiant_sources = allocate_solar
    no_iw.allocate_exterior_radiant_sources = allocate_solar
    try:
        yield
    finally:
        orchestration.allocate_internal_radiant_source = original_o
        no_iw.allocate_internal_radiant_source = original_n
        orchestration.allocate_exterior_radiant_sources = original_oe
        no_iw.allocate_exterior_radiant_sources = original_ne


def _simulate_with_forcing_trace(s: Scenario):
    solar = modelica_solar()
    runner = run_thermostat_case if s.topology == "IW" else run_thermostat_case_no_iw
    applied_solar: list[float] = []
    with _source_crosswalk(s):
        result = runner(
            _case(s), index=INDEX, gains_w=200.0, occupancy_fraction=ONES,
            heating_setpoint_schedule=ONES*20.0, cooling_setpoint_schedule=ONES*27.0,
            heating_availability_schedule=ONES.astype(bool),
            cooling_availability_schedule=ONES.astype(bool),
            ventilation_fraction_schedule=ZEROS, heat_recovery_efficiency_schedule=ZEROS,
            hourly_input_transform=_transform(s, solar, applied_solar),
        )
    return result, np.asarray(applied_solar)


def simulate(s: Scenario):
    result, _ = _simulate_with_forcing_trace(s)
    return result


def scenarios():
    return [
        Scenario("V0", "audited starting point: inferred 96 m² IW and area allocation"),
        Scenario("V1a", "allocation only: retain IW topology, send solar to AW", solar_aw=1.0),
        Scenario("V1b", "topology only relative to V1a: remove IW, retain all-AW solar", topology="no-IW", solar_aw=1.0),
        Scenario("V2", "matched Modelica solar-node fractions", solar_air=ISO_F_AIR, solar_aw=ISO_F_AW),
        Scenario("V3", "U-value-controlled envelope reduction", solar_air=ISO_F_AIR, solar_aw=ISO_F_AW, construction_mode="U-controlled"),
        Scenario("V4", "matched inside surface coefficient", solar_air=ISO_F_AIR, solar_aw=ISO_F_AW, construction_mode="U-controlled", inside_h=9.1),
        Scenario("V5", "harmonised long-wave boundary", solar_air=ISO_F_AIR, solar_aw=ISO_F_AW, construction_mode="U-controlled", inside_h=9.1, neutral_longwave=True),
        Scenario("V6", "matched 200 W internal-gain split", solar_air=ISO_F_AIR, solar_aw=ISO_F_AW, internal_air=0.5, internal_aw=0.5*ISO_F_AW/(ISO_F_AW+ISO_F_IW), construction_mode="U-controlled", inside_h=9.1, neutral_longwave=True),
        Scenario("V7", "floor and airflow provenance resolved: comparator values retained", solar_air=ISO_F_AIR, solar_aw=ISO_F_AW, internal_air=0.5, internal_aw=0.5*ISO_F_AW/(ISO_F_AW+ISO_F_IW), construction_mode="U-controlled", inside_h=9.1, neutral_longwave=True, ach=0.414),
    ]


def run_all():
    OUT.mkdir(parents=True, exist_ok=True)
    solar = modelica_solar()
    rows, hourly = [], []
    for s in scenarios():
        sim = simulate(s)
        load = np.array([r.total_hvac_load_w for r in sim.hourly_results])
        heat, cool = np.clip(load, 0, None), np.clip(-load, 0, None)
        rows.append(dict(scenario=s.name, interpretation=s.interpretation,
            topology=s.topology, construction_mode=s.construction_mode,
            solar_f_air=s.solar_air,
            solar_f_AW=(1-s.solar_air)*(s.solar_aw if s.solar_aw is not None else np.nan),
            solar_f_IW=(1-s.solar_air)*(1-s.solar_aw) if s.solar_aw is not None else np.nan,
            internal_f_air=s.internal_air, inside_h_W_m2K=s.inside_h,
            neutral_longwave=s.neutral_longwave, infiltration_ACH=s.ach,
            annual_solar_MWh=solar.sum()/1e6, heating_MWh=heat.sum()/1e6,
            cooling_MWh=cool.sum()/1e6, peak_heating_kW=heat.max()/1000,
            peak_cooling_kW=cool.max()/1000,
            maximum_balance_residual_W=sim.maximum_absolute_balance_residual_w))
        hourly.extend(dict(timestamp=t, scenario=s.name, modelica_solar_gain_W=sw,
                           HVAC_load_W=q, heating_load_W=max(q,0), cooling_load_W=max(-q,0))
                      for t, sw, q in zip(INDEX, solar, load))
    summary = pd.DataFrame(rows)
    comparison = {"V0": None, "V1a": "V0", "V1b": "V1a", "V2": "V0",
                  "V3": "V2", "V4": "V3", "V5": "V4", "V6": "V5", "V7": "V6"}
    indexed = summary.set_index("scenario")
    summary["compare_to"] = summary.scenario.map(comparison)
    summary["delta_heating_MWh"] = [
        np.nan if comparison[n] is None else indexed.at[n, "heating_MWh"]-indexed.at[comparison[n], "heating_MWh"]
        for n in summary.scenario]
    summary["delta_cooling_MWh"] = [
        np.nan if comparison[n] is None else indexed.at[n, "cooling_MWh"]-indexed.at[comparison[n], "cooling_MWh"]
        for n in summary.scenario]
    hourly = pd.DataFrame(hourly)
    summary.to_csv(OUT / "case600_vdi_crosswalk_summary.csv", index=False)
    hourly.to_csv(OUT / "case600_vdi_crosswalk_hourly.csv", index=False)
    return summary, hourly


def _factor_levels():
    return {
        "topology": ("IW", "no-IW"),
        "source_allocation": ("VDI-area", "Modelica-fractions"),
        "envelope": ("layer-controlled", "U-controlled"),
        "inside_h": (8.0, 9.1),
        "longwave": ("explicit-VDI", "harmonised"),
        "internal_gain": ("all-air", "Modelica-split"),
    }


def _factorial_scenario(run_number, f, solar_group="modelica"):
    no_iw_topology = f["topology"] == "no-IW"
    matched_source = f["source_allocation"] == "Modelica-fractions"
    matched_internal = f["internal_gain"] == "Modelica-split"
    solar_air = ISO_F_AIR if matched_source else 0.0
    solar_aw = ((1.0-solar_air) if no_iw_topology else ISO_F_AW) if matched_source else None
    internal_air = 0.5 if matched_internal else 1.0
    internal_aw = ((1.0-internal_air) if no_iw_topology else
                   0.5*ISO_F_AW/(ISO_F_AW+ISO_F_IW)) if matched_internal else None
    return Scenario(
        name=f"F{run_number:02d}", interpretation="full-factorial screening",
        topology=f["topology"], solar_air=solar_air, solar_aw=solar_aw,
        internal_air=internal_air, internal_aw=internal_aw,
        construction_mode=f["envelope"], inside_h=f["inside_h"],
        neutral_longwave=f["longwave"] == "harmonised", ach=0.414,
        solar_group=solar_group,
    )


def run_factorial():
    """Run the 2^6 screening design using only established crosswalk switches."""
    OUT.mkdir(parents=True, exist_ok=True)
    solar = modelica_solar()
    factor_levels = _factor_levels()
    keys = tuple(factor_levels)
    combinations = list(product(*(factor_levels[k] for k in keys)))
    rows = []
    for run_number, values in enumerate(combinations, 1):
        f = dict(zip(keys, values))
        scenario = _factorial_scenario(run_number, f)
        sim, applied = _simulate_with_forcing_trace(scenario)
        assert np.array_equal(applied, solar), scenario.name
        load = np.asarray([r.total_hvac_load_w for r in sim.hourly_results])
        heat_mwh = np.clip(load, 0, None).sum()/1e6
        cool_mwh = np.clip(-load, 0, None).sum()/1e6
        rows.append(dict(run=scenario.name, **f, annual_solar_MWh=applied.sum()/1e6,
                         heating_EUI=heat_mwh*1000/AREA,
                         cooling_EUI=cool_mwh*1000/AREA))

    result = pd.DataFrame(rows)
    assert len(result) == np.prod([len(v) for v in factor_levels.values()])
    assert result.annual_solar_MWh.nunique() == 1
    assert np.isfinite(result[["annual_solar_MWh", "heating_EUI", "cooling_EUI"]]).all().all()
    h_low, h_high = (3.75*1000/AREA, 4.98*1000/AREA)
    c_low, c_high = (5.00*1000/AREA, 6.83*1000/AREA)
    result["heating_in_range"] = result.heating_EUI.between(h_low, h_high, inclusive="both")
    result["cooling_in_range"] = result.cooling_EUI.between(c_low, c_high, inclusive="both")
    result["both_in_range"] = result.heating_in_range & result.cooling_in_range
    result["d_heating_EUI"] = np.maximum.reduce([h_low-result.heating_EUI,
                                                   np.zeros(len(result)),
                                                   result.heating_EUI-h_high])
    result["d_cooling_EUI"] = np.maximum.reduce([c_low-result.cooling_EUI,
                                                   np.zeros(len(result)),
                                                   result.cooling_EUI-c_high])
    result["D_EUI"] = np.hypot(result.d_heating_EUI, result.d_cooling_EUI)
    result["D_EUI_norm"] = np.hypot(result.d_heating_EUI/(h_high-h_low),
                                     result.d_cooling_EUI/(c_high-c_low))
    result = result.sort_values(["both_in_range", "D_EUI_norm"],
                                ascending=[False, True], kind="stable").reset_index(drop=True)
    result.to_csv(OUT / "factorial_eui_summary.csv", index=False)
    bounds = {"heating": (h_low, h_high), "cooling": (c_low, c_high)}
    return result, factor_levels, bounds


def run_dual_solar_factorial():
    """Run identical 2^6 designs under Modelica and native-VDI solar."""
    OUT.mkdir(parents=True, exist_ok=True)
    reference_solar = modelica_solar()
    levels = _factor_levels()
    keys = tuple(levels)
    combinations = list(product(*(levels[k] for k in keys)))
    rows = []
    for solar_group in ("modelica", "native_vdi"):
        for run_number, values in enumerate(combinations, 1):
            factors = dict(zip(keys, values))
            scenario = _factorial_scenario(run_number, factors, solar_group)
            sim, applied = _simulate_with_forcing_trace(scenario)
            if solar_group == "modelica":
                assert np.array_equal(applied, reference_solar), scenario.name
                annual_solar = applied.sum()/1e6
            else:
                assert applied.size == 8760, scenario.name
                annual_solar = applied.sum()/1e6
            load = np.asarray([r.total_hvac_load_w for r in sim.hourly_results])
            rows.append(dict(
                solar_group=solar_group, factorial_id=scenario.name, **factors,
                annual_solar_MWh=annual_solar,
                heating_MWh=np.clip(load, 0, None).sum()/1e6,
                cooling_MWh=np.clip(-load, 0, None).sum()/1e6,
            ))
    result = pd.DataFrame(rows)
    expected = 2*np.prod([len(v) for v in levels.values()])
    assert len(result) == expected
    assert result.groupby("solar_group").size().eq(len(combinations)).all()
    assert result.groupby("factorial_id").size().eq(2).all()
    assert result.groupby("solar_group").annual_solar_MWh.nunique().eq(1).all()
    assert np.isfinite(result[["annual_solar_MWh", "heating_MWh", "cooling_MWh"]]).all().all()

    h_low, h_high = 3.75, 4.98
    c_low, c_high = 5.00, 6.83
    result["heating_in_range"] = result.heating_MWh.between(h_low, h_high, inclusive="both")
    result["cooling_in_range"] = result.cooling_MWh.between(c_low, c_high, inclusive="both")
    result["both_in_range"] = result.heating_in_range & result.cooling_in_range
    d_h = np.maximum.reduce([h_low-result.heating_MWh, np.zeros(len(result)),
                             result.heating_MWh-h_high])
    d_c = np.maximum.reduce([c_low-result.cooling_MWh, np.zeros(len(result)),
                             result.cooling_MWh-c_high])
    result["D_MWh_norm"] = np.hypot(d_h/(h_high-h_low), d_c/(c_high-c_low))
    result = result.sort_values(["solar_group", "both_in_range", "D_MWh_norm"],
                                ascending=[True, False, True], kind="stable").reset_index(drop=True)

    for group in ("modelica", "native_vdi"):
        result[result.solar_group == group].to_csv(
            OUT / f"factorial_mwh_summary_{group}.csv", index=False)
    paired = result.pivot(index="factorial_id", columns="solar_group",
                          values=["heating_MWh", "cooling_MWh", "D_MWh_norm"])
    paired.columns = [f"{metric}_{group}" for metric, group in paired.columns]
    paired["delta_heating_MWh"] = paired.heating_MWh_native_vdi-paired.heating_MWh_modelica
    paired["delta_cooling_MWh"] = paired.cooling_MWh_native_vdi-paired.cooling_MWh_modelica
    paired["delta_D_MWh_norm"] = paired.D_MWh_norm_native_vdi-paired.D_MWh_norm_modelica
    paired = paired.reset_index()
    paired.to_csv(OUT / "factorial_mwh_paired_solar_comparison.csv", index=False)
    return result, paired, levels
