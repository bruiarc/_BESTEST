"""Reproducible Case 600 VDI four-case validation and remaining audits."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DEV = HERE.parents[2]
INPUTS = HERE / "inputs"
BESTEST = HERE.parent
sys.path.insert(0, str(DEV / "RC_br"))

from RClib.vdi6007 import RCCase, run_thermostat_case
from RClib.vdi6007._BR_ import build_hourly_inputs
from RClib.vdi6007.case_adapter import VDIAdapterDefaults
from RClib.vdi6007.no_iw import (
    prepare_model_case_no_iw_from_prepared,
    run_thermostat_case_no_iw,
    run_thermostat_model_no_iw,
)
from RClib.vdi6007.state import zero_storage_state

AREA = 48.0
VOLUME = 129.6
RHO = 1.20
CP = 1005.0
HEAT_RANGE = (3.75, 4.98)
COOL_RANGE = (5.00, 6.83)
INDEX = pd.date_range("2023-01-01", periods=8760, freq="h")
ONES = np.ones(8760)
ZEROS = np.zeros(8760)
WEATHER = DEV / "2_validation/modelica_test_2/modelica-buildings-github-master/Buildings/Resources/weatherdata/USA_CO_Denver.Intl.AP.725650_TMY3.epw"
SOLAR_FILE = BESTEST / "results/case600/case600_iso13790_diagnostic_modelica_solar_hourly.csv"
OUT4 = HERE / "results/case600_vdi_four_case"
OUTS = HERE / "results/case600_vdi_remaining_sensitivity"


def make_case(*, inside=8.0, heat_conv=1.00, cool_conv=1.00,
              internal_conv=1.00):
    defaults = VDIAdapterDefaults(
        inside_total_coefficient_w_m2k=inside,
        heating_convective_fraction=heat_conv,
        cooling_convective_fraction=cool_conv,
        internal_gain_convective_fraction=internal_conv,
    )
    return RCCase(
        year=2023,
        loc_json=INPUTS / "case600_location.json",
        geo_json=INPUTS / "case600_geometry.json",
        default_json=INPUTS / "case600_defaults.json",
        epw_path=WEATHER,
        occupancy_profile_csv=INPUTS / "case600_occupancy.csv",
        adapter_defaults=defaults,
        use_construction_properties=True,
    )


def solar_series():
    frame = pd.read_csv(SOLAR_FILE)
    assert len(frame) == 8760
    assert np.array_equal(frame.timestamp_s.to_numpy(), np.arange(1, 8761) * 3600.0)
    return frame.solar_gain_W.to_numpy(float)


def transform(ach, controlled=True):
    sol = solar_series()
    resistance = 1.0 / (RHO * CP * ach * VOLUME / 3600.0)

    def apply(position, hourly):
        item = replace(hourly, ventilation_resistance_k_w=resistance)
        if not controlled:
            return item
        # Disable both native VDI short-wave paths, then inject one aggregate source.
        boundaries = tuple(replace(b, direct_surface_irradiance_w_m2=0.0,
                                   diffuse_surface_irradiance_w_m2=0.0)
                           for b in item.boundary_inputs)
        return replace(item, boundary_inputs=boundaries, exterior_radiant_sources=(),
                       internal_radiant_gain_w=item.internal_radiant_gain_w + float(sol[position]))
    return apply


def simulate(*, topology="no-IW", ach=0.414, controlled=True, inside=8.0,
             heat_conv=1.00, cool_conv=1.00, internal_conv=1.00,
             initial_state=None):
    case = make_case(inside=inside, heat_conv=heat_conv, cool_conv=cool_conv,
                     internal_conv=internal_conv)
    runner = run_thermostat_case_no_iw if topology == "no-IW" else run_thermostat_case
    return runner(
        case, index=INDEX, gains_w=200.0, occupancy_fraction=ONES,
        heating_setpoint_schedule=ONES * 20.0, cooling_setpoint_schedule=ONES * 27.0,
        heating_availability_schedule=ONES.astype(bool), cooling_availability_schedule=ONES.astype(bool),
        ventilation_fraction_schedule=ZEROS, heat_recovery_efficiency_schedule=ZEROS,
        hourly_input_transform=transform(ach, controlled), initial_state=initial_state,
    )


def metrics(name, sim, solar_source, annual_solar):
    load = np.array([r.total_hvac_load_w for r in sim.hourly_results])
    heat = np.clip(load, 0, None)
    cool = np.clip(-load, 0, None)
    hm, cm = heat.sum()/1e6, cool.sum()/1e6
    return dict(case=name, heating_MWh=hm, cooling_MWh=cm, total_HVAC_MWh=hm+cm,
                heating_EUI_kWh_m2yr=hm*1000/AREA, cooling_EUI_kWh_m2yr=cm*1000/AREA,
                total_EUI_kWh_m2yr=(hm+cm)*1000/AREA, peak_heating_kW=heat.max()/1000,
                peak_cooling_kW=cool.max()/1000, heating_hours=int((heat > 1e-8).sum()),
                cooling_hours=int((cool > 1e-8).sum()), annual_solar_MWh=annual_solar,
                solar_source=solar_source, heating_pass=HEAT_RANGE[0] <= hm <= HEAT_RANGE[1],
                cooling_pass=COOL_RANGE[0] <= cm <= COOL_RANGE[1],
                combined_pass=(HEAT_RANGE[0] <= hm <= HEAT_RANGE[1] and COOL_RANGE[0] <= cm <= COOL_RANGE[1]),
                maximum_balance_residual_W=sim.maximum_absolute_balance_residual_w)


def run_four_cases():
    OUT4.mkdir(parents=True, exist_ok=True)
    sol_mwh = solar_series().sum()/1e6
    specs = [
        ("A", "96 m2 IW", 0.414, 1.00, 1.00,
         "100% convective HVAC and internal gains"),
        ("B", "no-IW", 0.414, 1.00, 1.00,
         "100% convective HVAC and internal gains"),
    ]
    rows, native_rows, hourly = [], [], []
    for label, topology, ach, heat_conv, cool_conv, split_label in specs:
        controlled = simulate(topology=topology, ach=ach, controlled=True,
                              heat_conv=heat_conv, cool_conv=cool_conv)
        rows.append(metrics(label, controlled, "Modelica aggregate controlled forcing", sol_mwh) |
                    {"topology": topology, "infiltration_ACH": ach,
                     "heating_convective_fraction": heat_conv,
                     "cooling_convective_fraction": cool_conv,
                     "internal_gain_convective_fraction": 1.0,
                     "HVAC_split": split_label})
        native = simulate(topology=topology, ach=ach, controlled=False,
                          heat_conv=heat_conv, cool_conv=cool_conv)
        # Native applied solar is the sum of the hourly allocations diagnosed by the engine.
        native_sol = sum(r.diagnostics.radiant_allocation.aw_source_w + r.diagnostics.radiant_allocation.iw_source_w
                         for r in native.hourly_results)/1e6
        native_rows.append(metrics(label, native, "native VDI solar", native_sol) |
                           {"topology": topology, "infiltration_ACH": ach,
                            "heating_convective_fraction": heat_conv,
                            "cooling_convective_fraction": cool_conv,
                            "internal_gain_convective_fraction": 1.0,
                            "HVAC_split": split_label})
        for ts, result, sw in zip(INDEX, controlled.hourly_results, solar_series()):
            hourly.append(dict(timestamp=ts, case=label, topology=topology, infiltration_ACH=ach,
                               heating_convective_fraction=heat_conv,
                               cooling_convective_fraction=cool_conv,
                               internal_gain_convective_fraction=1.0,
                               HVAC_split=split_label,
                               zone_temperature_C=result.indoor_air_temperature_c,
                               operative_temperature_C=result.operative_temperature_c,
                               HVAC_load_W=result.total_hvac_load_w,
                               heating_load_W=max(result.total_hvac_load_w, 0),
                               cooling_load_W=max(-result.total_hvac_load_w, 0), solar_gain_W=sw))
    # Reference comparator is read from its simulation output, never hard-coded.
    met = pd.read_csv(BESTEST / "results/case600/case600_metrics.csv")
    def mv(metric):
        q = met[(met.implementation == "modelica") & (met.run_mode == "native") & (met.metric == metric)]
        return float(q.value.iloc[0])
    mh, mc = mv("annual_heating_energy"), mv("annual_cooling_energy")
    mph, mpc = mv("peak_heating_load"), mv("peak_cooling_load")
    ref = dict(case="Modelica native comparator", topology="ISO13790 5R1C", infiltration_ACH=0.414,
               heating_convective_fraction=1.0, cooling_convective_fraction=1.0,
               internal_gain_convective_fraction=1.0,
               HVAC_split="100% convective (native Modelica connector)",
               heating_MWh=mh, cooling_MWh=mc, total_HVAC_MWh=mh+mc,
               heating_EUI_kWh_m2yr=mh*1000/AREA, cooling_EUI_kWh_m2yr=mc*1000/AREA,
               total_EUI_kWh_m2yr=(mh+mc)*1000/AREA, peak_heating_kW=mph, peak_cooling_kW=mpc,
               heating_hours=np.nan, cooling_hours=np.nan, annual_solar_MWh=sol_mwh,
               solar_source="Modelica native", heating_pass=HEAT_RANGE[0] <= mh <= HEAT_RANGE[1],
               cooling_pass=COOL_RANGE[0] <= mc <= COOL_RANGE[1],
               combined_pass=(HEAT_RANGE[0] <= mh <= HEAT_RANGE[1] and COOL_RANGE[0] <= mc <= COOL_RANGE[1]),
               maximum_balance_residual_W=np.nan)
    controlled_df = pd.DataFrame(rows + [ref])
    native_df = pd.DataFrame(native_rows)
    hourly_df = pd.DataFrame(hourly)
    controlled_df.to_csv(OUT4 / "case600_vdi_four_case_results.csv", index=False)
    native_df.to_csv(OUT4 / "case600_vdi_four_case_native_solar_results.csv", index=False)
    hourly_df.to_csv(OUT4 / "case600_vdi_four_case_hourly_controlled.csv", index=False)
    return controlled_df, native_df, hourly_df


def run_sensitivities():
    OUTS.mkdir(parents=True, exist_ok=True)
    split_rows = []
    for kind, values in (("heating", [1,.8,.6,.4,.2,0]), ("cooling", [1,.8,.6,.4,.3,.2,0])):
        for fraction in values:
            # derive_hvac_fractions currently produces -1.11e-16 at an exact
            # zero after area-weighted subtraction. Preserve that finding and
            # use the requested labelled epsilon only for this endpoint.
            run_fraction = 1e-9 if fraction == 0 else fraction
            sim = simulate(heat_conv=run_fraction if kind == "heating" else 1.0,
                           cool_conv=run_fraction if kind == "cooling" else 1.0)
            row = metrics(f"{kind}_{fraction:.1f}", sim, "Modelica aggregate controlled forcing", solar_series().sum()/1e6)
            row.update(sensitivity=kind, convective_fraction=fraction, radiant_fraction=1-fraction,
                       zero_fraction_treatment=("1e-9 numerical diagnostic: exact zero rejected by floating residual in derive_hvac_fractions"
                                                if fraction == 0 else "exact"))
            split_rows.append(row)
    split = pd.DataFrame(split_rows)
    split.to_csv(OUTS / "case600_vdi_hvac_split_sensitivity.csv", index=False)

    surface_rows = []
    # 7.7 = ISO 6946 conventional combined value; 8.0 current closure; 9.1 Modelica hSur comparator.
    for inside, source in [(7.7, "ISO 6946 Rsi=0.13 conventional total"),
                           (8.0, "current VDI closure"), (9.1, "Modelica Zone5R1C hSur comparator")]:
        sim = simulate(inside=inside)
        surface_rows.append(metrics(str(inside), sim, "Modelica aggregate controlled forcing", solar_series().sum()/1e6) |
                            {"inside_total_coefficient_W_m2K": inside, "evidence": source,
                             "interpretation": "combined coefficient; RClib subtracts fixed 5 W/m2K radiation to obtain convection"})
    pd.DataFrame(surface_rows).to_csv(OUTS / "case600_vdi_surface_coefficient_sensitivity.csv", index=False)

    floor = pd.DataFrame([
        {"construction":"1.003 m massless insulation proxy + 25 mm timber", "boundary_condition":"Outdoors in current VDI input",
         "surface_films":"Rsi implicit in U target; Rse=0.04 used by adapter reduction", "thermal_storage":"timber only; insulation rho*cp=1e-18",
         "candidate_VDI_classification":"AW, but boundary must represent BESTEST adiabatic floor", "BESTEST_Modelica_treatment":"UFlo=0.038, AFlo=48, b=1 to outdoor node",
         "status":"model-form/boundary representation requires care; do not change for fit"}])
    floor.to_csv(OUTS / "case600_vdi_floor_boundary_audit.csv", index=False)

    case = make_case()
    pm = case.adapted.prepared_model
    aw = pm.geometry.aw_surface_area_m2
    allocation = pd.DataFrame([
        {"topology":"96 m2 IW", "AW_area_m2":aw, "IW_area_m2":96.0, "total_receiving_area_m2":aw+96,
         "AW_weight":aw/(aw+96), "IW_weight":96/(aw+96), "injection":"internal_radiant_gain_w"},
        {"topology":"no-IW", "AW_area_m2":aw, "IW_area_m2":0.0, "total_receiving_area_m2":aw,
         "AW_weight":1.0, "IW_weight":0.0, "injection":"internal_radiant_gain_w"},
    ])
    allocation.to_csv(OUTS / "case600_vdi_radiative_allocation_audit.csv", index=False)

    cold = simulate()
    warm = simulate(initial_state=cold.final_state)
    def period(sim, hours):
        load=np.array([r.total_hvac_load_w for r in sim.hourly_results])[:hours]
        return np.clip(load,0,None).sum()/1e6, np.clip(-load,0,None).sum()/1e6
    init=[]
    for label, sim in [("20C zero-history", cold), ("one repeated-year warm-up", warm)]:
        annual=period(sim,8760); week=period(sim,168); month=period(sim,744)
        init.append({"initialization":label,"annual_heating_MWh":annual[0],"annual_cooling_MWh":annual[1],
                     "first_week_heating_MWh":week[0],"first_week_cooling_MWh":week[1],
                     "first_month_heating_MWh":month[0],"first_month_cooling_MWh":month[1]})
    pd.DataFrame(init).to_csv(OUTS / "case600_vdi_initialization_sensitivity.csv", index=False)

    base = metrics("baseline", cold, "Modelica aggregate controlled forcing", solar_series().sum()/1e6)
    summary = pd.DataFrame([
      ["HVAC convective/radiant split","H 100/0; C 100/0","requested comparison baseline",False,True,"pure convective heaPorAir", "see split CSV","case-dependent","case-dependent","high","high","cross-model closure assumption"],
      ["solar/radiative redistribution","AW/IW area allocation","RClib sources.py",False,True,"ISO surface/mass allocation", "topology-material","unresolved","unresolved","medium","high","likely implementation issue"],
      ["inside surface coefficient","8 W/m2K","VDIAdapterDefaults",False,True,"hSur=9.1 W/m2K", "see coefficient CSV","see CSV","see CSV","medium","medium","cross-model closure assumption"],
      ["exterior films/U consistency","Rse=0.04; U prescribed","defaults JSON",True,True,"U parameters directly used", "audit only","possible increase if duplicated","possible decrease","high","high","UNRESOLVED"],
      ["floor boundary","AW outdoors, U=0.038","defaults JSON",True,True,"AFlo=48, UFlo=.038, b=1", "audit only","unresolved","unresolved","medium","high","model-form difference"],
      ["long-wave exterior","EPW HIR, eps .90/.93","RClib boundary",False,True,"ISO13790 exterior equivalent boundary omits explicit LW", "not isolated","possible increase","possible decrease","medium","medium","model-form difference"],
      ["initialization","20C zero history","RClib state",False,True,"Modelica initial equations", "see initialization CSV","see CSV","see CSV","high","low","low-impact assumption"],
      ["ventilation air properties","rho=1.20, cp=1005; 0.414 ACH","VDIAdapterDefaults",False,True,"airRat=.414 in Zone5R1C", "G=%.3f W/K"%(RHO*CP*.414*VOLUME/3600),"higher ACH raises","higher ACH lowers","high","medium","cross-model closure assumption"],
      ["internal sensible split","100/0 convective/radiant","requested comparison baseline",True,True,"Zone5R1C phiAir k=.5 then surface/mass split", "not swept","n/a","n/a","medium","high","cross-model closure assumption"],
    ], columns=["parameter","baseline value","source","BESTEST prescribed?","VDI required?","Modelica comparator treatment","sensitivity magnitude","direction of heating change","direction of cooling change","physical plausibility","priority","status"])
    summary.to_csv(OUTS / "case600_vdi_remaining_parameter_summary.csv", index=False)
    return split, pd.DataFrame(surface_rows), allocation, pd.DataFrame(init), summary


if __name__ == "__main__":
    controlled, native, _ = run_four_cases()
    split, surface, allocation, init, summary = run_sensitivities()
    print(controlled[["case","heating_MWh","cooling_MWh","heating_pass","cooling_pass"]].to_string(index=False))
    print("outputs:", OUT4, OUTS)
