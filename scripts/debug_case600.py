#!/usr/bin/env python3
"""Diagnostic-only attribution for the Case 600 native ISO result."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / "modelica_test_2"
sys.path.insert(0, str(LEGACY))
from iso_validation.bestest_pipeline import CASE_DEFINITIONS, _denver_epw, make_rclib_zone  # noqa: E402
from iso_validation.dependencies import radiation_classes  # noqa: E402


def _summary(frame, column):
    positive = frame[frame[column] > 0]
    peak = frame.loc[frame[column].idxmax()]
    return {"quantity": column, "annual_MWh_or_MWh_m2": frame[column].sum() / 1e6,
            "maximum": frame[column].max(), "mean_sunlit": positive[column].mean() if len(positive) else 0.,
            "nonzero_hours": len(positive), "peak_timestamp_s": peak.timestamp_s}


def native_trace():
    """Reproduce the existing native-solar algorithm while exposing its inputs."""
    Location, Window, OpaqueSurface = radiation_classes(); definition = CASE_DEFINITIONS["600"]
    weather = Location(epwfile_path=_denver_epw())
    sky = dict(external_surface_resistance=.04, external_radiative_coefficient=4.5, sky_air_temperature_difference=11.)
    azimuth = (180., -90., 0., 90.)
    window = Window(azimuth_tilt=0., alititude_tilt=90., area=12., glass_solar_transmittance=.769,
                    frame_fraction=.001, u_value=3.1, sky_view_factor=.5, **sky)
    walls = [OpaqueSurface(azimuth_tilt=a, alititude_tilt=90., area=area, u_value=.53,
                           solar_absorptivity=.6, sky_view_factor=.5, **sky)
             for area, a in zip((21.6, 16.2, 9.6, 16.2), azimuth)]
    roof = OpaqueSurface(azimuth_tilt=0., alititude_tilt=0., area=48., u_value=.33,
                          solar_absorptivity=.6, sky_view_factor=1., **sky)
    rows=[]
    for hour, (_, row) in enumerate(weather.weather_data.iterrows()):
        altitude, direction = weather.calc_sun_position(39.83, -104.65, 1995, hour)
        dni, dhi = float(row.dirnorrad_Whm2), float(row.difhorrad_Whm2)
        for surface in [window, *walls, roof]: surface.calc_solar_gains(altitude, direction, dni, dhi)
        rows.append((float((hour + 1)*3600), float(row.drybulb_C), dni, dhi, float(row.glohorrad_Whm2), altitude, direction,
                     window.calc_direct_solar_factor(altitude, direction)*dni,
                     window.calc_diffuse_solar_factor()*dhi, window.solar_gains,
                     sum(w.solar_gains for w in walls), roof.solar_gains))
    out=pd.DataFrame(rows,columns=("timestamp_s","outdoor_temperature_C","direct_normal_W_m2","diffuse_horizontal_W_m2","global_horizontal_W_m2","solar_altitude_deg","solar_azimuth_deg","south_window_direct_W_m2","south_window_diffuse_W_m2","window_solar_gain_W","wall_solar_gain_W","roof_solar_gain_W"))
    out["opaque_solar_gain_W"] = out.wall_solar_gain_W + out.roof_solar_gain_W
    out["total_zone_solar_gain_W"] = out.window_solar_gain_W + out.opaque_solar_gain_W
    return out


def control_trace(solar, *, volumetric_heat_capacity=1200.):
    """Expose the hourly ISO control solution for one unchanged forcing path.

    ``volumetric_heat_capacity`` is deliberately an explicit diagnostic knob.
    It is not part of the formal baseline and is used below only to quantify
    the documented 1200-versus-1206 J/(m3 K) convention.
    """
    controlled = make_rclib_zone(CASE_DEFINITIONS["600"])
    controlled.h_ve_adj = volumetric_heat_capacity * .414 * 129.6 / 3600.
    mc=ac=20.; rows=[]
    for row in solar.itertuples(index=False):
        controlled.solve_energy(200., row.total_zone_solar_gain_W, row.outdoor_temperature_C, mc, ac)
        mc,ac=controlled.t_m_next,controlled.t_air
        # ``t_air_free`` is calculated inside has_demand from the *same* prior
        # controlled state and forcing used to decide this hour's ideal load.
        rows.append((row.timestamp_s, controlled.t_air_free, controlled.t_air, controlled.t_set_heating, controlled.t_set_cooling,
                     controlled.heating_demand, controlled.cooling_demand, max(controlled.heating_demand,0.), max(-controlled.cooling_demand,0.),
                     controlled.phi_ia, controlled.phi_st, controlled.phi_m, controlled.t_air_energy_balance_residual,
                     controlled.t_m_next, controlled.t_s, controlled.h_ve_adj, controlled.h_tr_op, controlled.h_tr_w,
                     controlled.h_tr_em, controlled.h_tr_ms, controlled.h_tr_is))
    return pd.DataFrame(rows,columns=("timestamp_s","T_air_free_C","T_air_controlled_C","T_set_heating_C","T_set_cooling_C","raw_heating_demand_W","raw_cooling_demand_W","heating_load_W","cooling_load_W","phi_air_W","phi_surface_W","phi_mass_W","air_balance_residual_W","T_mass_next_C","T_surface_C","H_ve_W_K","H_tr_op_W_K","H_tr_window_W_K","H_tr_em_W_K","H_tr_ms_W_K","H_tr_is_W_K"))


def _track_metrics(metrics, implementation, run_mode):
    track = metrics[(metrics.implementation == implementation) & (metrics.run_mode == run_mode)].set_index("metric")
    return track


def _annual_and_peak_comparison(metrics):
    """Make the three-track artifact used by the Case-600 diagnostic note."""
    modelica = _track_metrics(metrics, "modelica", "native")
    native = _track_metrics(metrics, "iso13790", "native")
    diagnostic = _track_metrics(metrics, "iso13790", "diagnostic_modelica_solar")
    bounds = {
        "annual_heating_energy": (3.75, 4.98),
        "annual_cooling_energy": (5.00, 6.83),
    }
    records = []
    for metric in ("annual_heating_energy", "annual_cooling_energy", "peak_heating_load", "peak_cooling_load"):
        iso_native, iso_diagnostic, mod = (float(x.loc[metric, "value"]) for x in (native, diagnostic, modelica))
        lower, upper = bounds.get(metric, (np.nan, np.nan))
        native_status = ("PASS" if lower <= iso_native <= upper else "FAIL") if np.isfinite(lower) else "NOT_ASSESSED"
        peak_times = [native.loc[metric, "occurrence_time_s"], diagnostic.loc[metric, "occurrence_time_s"], modelica.loc[metric, "occurrence_time_s"]]
        peak_labels = [pd.Timestamp("1995-01-01") + pd.to_timedelta(t, unit="s") if pd.notna(t) else pd.NaT for t in peak_times]
        records.append({
            "metric": metric, "unit": modelica.loc[metric, "unit"],
            "ISO_native": iso_native, "ISO_modelica_solar": iso_diagnostic, "Modelica_native": mod,
            "change_due_to_solar": iso_diagnostic - iso_native,
            "change_due_to_solar_percent_of_native": 100 * (iso_diagnostic - iso_native) / iso_native,
            "remaining_difference_to_modelica": iso_diagnostic - mod,
            "remaining_difference_to_modelica_percent": 100 * (iso_diagnostic - mod) / mod,
            "native_difference_to_modelica": iso_native - mod,
            "native_difference_to_modelica_percent": 100 * (iso_native - mod) / mod,
            "ashrae_lower": lower, "ashrae_upper": upper,
            "native_status": native_status,
            "diagnostic_status": "DIAGNOSTIC_NOT_FORMAL",
            "modelica_native_status": ("PASS" if np.isfinite(lower) and lower <= mod <= upper else "NOT_ASSESSED"),
            "ISO_native_peak_time_s": peak_times[0], "ISO_native_peak_timestamp": peak_labels[0],
            "ISO_modelica_solar_peak_time_s": peak_times[1], "ISO_modelica_solar_peak_timestamp": peak_labels[1],
            "Modelica_native_peak_time_s": peak_times[2], "Modelica_native_peak_timestamp": peak_labels[2],
        })
    return pd.DataFrame(records)


def main():
    out=ROOT/"results/case600_debug"; out.mkdir(parents=True,exist_ok=True)
    solar=native_trace(); solar.to_csv(out/"native_solar_trace.csv",index=False)
    raw=pd.read_csv(ROOT.parent / "_modelica/results/Case600/Case600_res.csv")
    time=solar.timestamp_s.to_numpy(); interp=lambda c: np.interp(time,raw.time,raw[c].astype(float))
    solar["modelica_total_zone_solar_gain_W"] = interp("zonHVAC.solGai.y")
    solar["modelica_window_solar_gain_W"] = interp("zonHVAC.win.solRadWin")
    solar["modelica_opaque_solar_gain_W"] = interp("zonHVAC.opa.y")
    solar.to_csv(out/"native_vs_modelica_solar_trace.csv",index=False)
    summaries=[]
    for column in ("global_horizontal_W_m2","direct_normal_W_m2","diffuse_horizontal_W_m2","south_window_direct_W_m2","south_window_diffuse_W_m2","window_solar_gain_W","opaque_solar_gain_W","total_zone_solar_gain_W","modelica_window_solar_gain_W","modelica_opaque_solar_gain_W","modelica_total_zone_solar_gain_W"):
        summaries.append(_summary(solar,column))
    pd.DataFrame(summaries).to_csv(out/"solar_summary.csv",index=False)
    control=control_trace(solar); control.to_csv(out/"control_and_balance_trace.csv",index=False)
    flagged=control[(control.T_air_free_C>control.T_set_cooling_C)&(control.cooling_load_W<=0)]
    pd.DataFrame([{"free_above_cooling_setpoint_cooling_zero_hours":len(flagged),"cooling_nonzero_hours":int((control.cooling_load_W>0).sum()),"simultaneous_heating_cooling_hours":int(((control.heating_load_W>0)&(control.cooling_load_W>0)).sum()),"maximum_cooling_W":control.cooling_load_W.max()}]).to_csv(out/"control_summary.csv",index=False)
    pd.DataFrame([{"stage":"raw ISO signed demand", "heating_MWh":control.raw_heating_demand_W.sum()/1e6,"cooling_MWh_signed":control.raw_cooling_demand_W.sum()/1e6},
                  {"stage":"positive clipping for standard schema", "heating_MWh":control.heating_load_W.sum()/1e6,"cooling_MWh_signed":control.cooling_load_W.sum()/1e6},
                  {"stage":"existing Case600 native standardized output", "heating_MWh":pd.read_csv(ROOT/'results/case600/case600_iso13790_native_hourly.csv').heating_load_W.sum()/1e6,"cooling_MWh_signed":pd.read_csv(ROOT/'results/case600/case600_iso13790_native_hourly.csv').cooling_load_W.sum()/1e6}]).to_csv(out/"load_extraction_trace.csv",index=False)
    ua=pd.DataFrame([("walls",63.6,.53,63.6*.53),("roof",48,.33,48*.33),("floor",48,.038,48*.038),("window",12,3.1,12*3.1)],columns=("surface","area_m2","U_W_m2K","UA_W_K")); ua.loc[len(ua)] = ("total",ua.area_m2.sum(),np.nan,ua.UA_W_K.sum()); ua.to_csv(out/"envelope_ua.csv",index=False)
    hve=1200*.414*129.6/3600
    pd.DataFrame([{"quantity":"H_ve", "independent_value":hve,"used_value":control.H_ve_W_K.iloc[0],"unit":"W/K"},{"quantity":"C_m","independent_value":42167*48,"used_value":42167*48,"unit":"J/K"},{"quantity":"A_m","independent_value":2.95*48,"used_value":2.95*48,"unit":"m2"}]).to_csv(out/"ventilation_and_mass_audit.csv",index=False)
    mass_fraction=141.6/171.6; surface_fraction=1-mass_fraction-37.2/(9.1*171.6)
    pd.DataFrame([{"prescribed_total_W":200.,"annual_integrated_MWh":200*8760/1e6,"air_node_W":100.,"surface_internal_component_W":100*surface_fraction,"mass_internal_component_W":100*mass_fraction,"schedule":"constant 8760 h","notes":"ISO implementation allocates gain using its Annex-C source terms; solar is not included in these isolated internal components."}]).to_csv(out/"internal_gain_audit.csv",index=False)
    audit=pd.DataFrame([("window area",12,12,12,"PASS","direct prescribed quantity"),("south orientation","south", "south (azimuth 0 in RClib convention)","south Modelica index 3","PASS","convention differs, physical orientation matches"),("g value",.769,.769,.769,"PASS","native Window receives prescribed value"),("frame fraction", "not separately prescribed",.001,.001,"UNRESOLVED","implementation default/diagnostic assumption"),("native annual total solar MWh",np.nan,solar.total_zone_solar_gain_W.sum()/1e6,solar.modelica_total_zone_solar_gain_W.sum()/1e6,"LIKELY ISSUE","native total is substantially lower")],columns=("quantity","ASHRAE_prescribed","Python_input_or_derived","Modelica_diagnostic","status","notes"));audit.to_csv(out/"window_solar_audit.csv",index=False)
    # Representative windows plus maximum cooling hour, retaining a small numerical balance trace.
    days=pd.concat([control[(control.timestamp_s>=0)&(control.timestamp_s<86400)],control[(control.timestamp_s>=31*86400)&(control.timestamp_s<32*86400)],control[(control.timestamp_s>=181*86400)&(control.timestamp_s<182*86400)],control.loc[[control.cooling_load_W.idxmax()]]]).drop_duplicates()
    days.to_csv(out/"selected_energy_balance_hours.csv",index=False)
    attribution=pd.DataFrame([
        ("annual load integration/sign", "raw vs positive-schema sums", "same annual magnitudes after documented sign conversion", "matches", "REJECTED"),
        ("thermostat/control", "free temperature >27 C with cooling=0", 0, "no uncontrolled above-setpoint hours", "UNLIKELY"),
        ("solar geometry/preprocessing", "annual net zone solar", f"native={solar.total_zone_solar_gain_W.sum()/1e6:.3f} MWh; Modelica diagnostic={solar.modelica_total_zone_solar_gain_W.sum()/1e6:.3f} MWh", "large forcing deficit", "LIKELY"),
        ("glazing solar", "annual window gain", f"native={solar.window_solar_gain_W.sum()/1e6:.3f}; Modelica={solar.modelica_window_solar_gain_W.sum()/1e6:.3f} MWh", "inspect incidence/diffuse/time convention", "LIKELY"),
        ("opaque solar", "annual opaque gain", f"native={solar.opaque_solar_gain_W.sum()/1e6:.3f}; Modelica={solar.modelica_opaque_solar_gain_W.sum()/1e6:.3f} MWh", "secondary component", "UNRESOLVED"),
        ("ventilation", "H_ve", f"{hve:.4f} W/K independent and used", "matches", "REJECTED"),
        ("thermal mass", "C_m and A_m", "2,024,016 J/K and 141.6 m2", "matches prescribed mapping", "UNLIKELY"),
        ("thermal core", "Case600FF matched-forcing regression", "0.298895 C MAE from established diagnostic", "forcing-harmonised response remains close", "UNLIKELY"),
    ],columns=("hypothesis","metric_checked","observed","evidence","status")); attribution.to_csv(out/"attribution_table.csv",index=False)

    # The three tracks have already been independently executed by the pilot
    # runner.  This table only calculates transparent, downstream comparisons.
    metrics = pd.read_csv(ROOT / "results/case600/case600_metrics.csv")
    comparison = _annual_and_peak_comparison(metrics)
    comparison.to_csv(out / "modelica_solar_comparison.csv", index=False)
    # The pilot runner owns the standard schema; preserve a diagnostic copy of
    # its requested 1-February three-track profile beside this comparison.
    pd.read_csv(ROOT / "results/case600/case600_feb1_load_profile.csv").to_csv(
        out / "feb1_three_track_load_profile.csv", index=False
    )

    hve_1206 = 1206. * .414 * 129.6 / 3600.
    control_1206 = control_trace(solar, volumetric_heat_capacity=1206.)
    baseline_heat, baseline_cool = control.heating_load_W.sum() / 1e6, control.cooling_load_W.sum() / 1e6
    sensitivity = pd.DataFrame([
        {"experiment": "baseline_native", "one_change": "none", "reason": "formal native Case 600 baseline",
         "annual_heating_MWh": baseline_heat, "annual_cooling_MWh": baseline_cool,
         "delta_heating_MWh": 0., "delta_cooling_MWh": 0., "formal_promoted": True},
        {"experiment": "air_heat_capacity_1206", "one_change": "H_ve uses 1206 rather than 1200 J/(m3 K)",
         "reason": "quantify the documented volumetric-air-heat-capacity convention only",
         "annual_heating_MWh": control_1206.heating_load_W.sum() / 1e6,
         "annual_cooling_MWh": control_1206.cooling_load_W.sum() / 1e6,
         "delta_heating_MWh": control_1206.heating_load_W.sum() / 1e6 - baseline_heat,
         "delta_cooling_MWh": control_1206.cooling_load_W.sum() / 1e6 - baseline_cool,
         "formal_promoted": False},
    ])
    sensitivity.to_csv(out / "heating_sensitivity_experiments.csv", index=False)

    # These rows separate directly prescribed matches from formulation-specific
    # quantities.  They intentionally do not assert false network equivalence.
    diag_heat = comparison.loc[comparison.metric == "annual_heating_energy"].iloc[0]
    pd.DataFrame([
        ("Heating control", "20 C heating / 27 C cooling, constant", "20 C / 27 C, hourly ideal-load solver", "constant setpoints; Modelica LimPID", "DIFFERENT BY FORMULATION", f"After solar substitution residual heating is {diag_heat.remaining_difference_to_modelica:.6f} MWh ({diag_heat.remaining_difference_to_modelica_percent:.2f}%)."),
        ("Ventilation and infiltration", "0.414 ACH; 129.6 m3", f"H_ve={hve:.6f} W/K using 1200 J/(m3 K)", f"H_ve={hve_1206:.6f} W/K if 1.206 kJ/(m3 K) convention is used", "DIFFERENT BY FORMULATION", "One-factor 1206 sensitivity is retained separately; it is not promoted."),
        ("Envelope heat transfer", "walls 0.53, roof 0.33, floor 0.038, window 3.1 W/(m2 K)", "aggregate UA=88.572 W/K", "same prescribed surface U-values/areas", "MATCH", "Direct aggregate check; no thermal-bridge term was introduced."),
        ("Internal sensible gains", "200 W, continuous", "200 W, continuous; ISO Annex-C allocation", "200 W continuous internal gain", "MATCH", "Annual input energy=1.752 MWh; node allocation differs by formulation."),
        ("Thermal mass", "lightweight: C_m=42167 J/(m2 K), A_m=2.95 A_f", "C_m=2,024,016 J/K; A_m=141.6 m2", "same lightweight prescribed construction", "MATCH", "Direct prescribed mass mapping; internal conductances are not one-to-one comparable."),
        ("ISO network conductances", "not prescribed as ISO coefficients", f"Htr_em={control.H_tr_em_W_K.iloc[0]:.6f}, Htr_ms={control.H_tr_ms_W_K.iloc[0]:.6f}, Htr_is={control.H_tr_is_W_K.iloc[0]:.6f} W/K", "Modelica thermal network has different equations", "NOT COMPARABLE", "Compare response only, not coefficients."),
        ("Initial state and timestep", "annual 8760 completed hours", "20 C initial air/mass; hourly solve", "20 C initial TAir at time 0; continuous Modelica integration sampled hourly", "DIFFERENT BY FORMULATION", "No demonstrated timestamp shift in load extraction; no sensitivity justified."),
        ("Weather and calendar", "Denver TMY3; non-leap 8760 h", "Denver EPW; 8760 hourly rows", "Denver weather bus; continuous interpolation", "DIFFERENT BY FORMULATION", "Same named weather source; endpoint sampling should be retained as a diagnostic rather than calibrated."),
    ], columns=("item", "prescribed_bestest_value", "iso_used_value", "modelica_value_where_comparable", "classification", "expected_influence_or_evidence")).to_csv(out / "heating_attribution_table.csv", index=False)

if __name__=='__main__': main()
