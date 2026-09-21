"""VDI BESTEST transfer runner: fixed F36/F52 logic, no per-case fitting."""

from __future__ import annotations

from dataclasses import dataclass, replace
from copy import deepcopy
from pathlib import Path
import json
import math
import tempfile
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BESTEST = HERE.parent
VDI = BESTEST / "2_vdi"
DEV = BESTEST.parents[1]
sys.path.insert(0, str(DEV / "RC_br"))

from RClib.vdi6007 import RCCase
from RClib.vdi6007.case_adapter import VDIAdapterDefaults
from RClib.vdi6007.no_iw import (
    prepare_model_case_no_iw_from_prepared,
    run_thermostat_case_no_iw,
)

AREA, VOLUME, RHO, CP = 48.0, 129.6, 1.20, 1005.0
INDEX = pd.date_range("2023-01-01", periods=8760, freq="h")
ONES, ZEROS = np.ones(8760), np.zeros(8760)
HEAT_BOUNDS_900, COOL_BOUNDS_900 = (1.04, 2.28), (2.35, 2.60)
WEATHER = BESTEST / "0_modelica/modelica-buildings-github-master/Buildings/Resources/weatherdata/USA_CO_Denver.Intl.AP.725650_TMY3.epw"
REFERENCE = BESTEST / "_ref/BESTEST_LBNL_EUI.md"
CASE600_RESULTS = BESTEST / "results/2_vdi/case600_vdi_crosswalk/factorial_mwh_summary_native_vdi.csv"
CONSTRUCTION_REGISTRY = BESTEST / "inputs/2_vdi/ashrae140_case_constructions.json"
PAIR_MAP = {"610":"910", "620":"920", "630":"930", "640":"940",
            "650":"950", "680":"980", "685":"985", "695":"995"}
ALL_CASES = ("600","610","620","630","640","650","660","670","680","685","695",
             "900","910","920","930","940","950","980","985","995")

CASE_PARENT = {
    "600":"base", "610":"600", "620":"600", "630":"620 + 610 shading",
    "640":"600", "650":"600", "660":"600", "670":"600", "680":"600",
    "685":"600", "695":"680 + 685 control", "900":"600", "910":"900",
    "920":"900", "930":"920 + 630 shading", "940":"900", "950":"900",
    "980":"900", "985":"900", "995":"980 + 685 control",
}

CASE_PAIR = {
    "600":"900", "610":"910", "620":"920", "630":"930", "640":"940",
    "650":"950", "660":None, "670":None, "680":"980", "685":"985",
    "695":"995", "900":"600", "910":"610", "920":"620", "930":"630",
    "940":"640", "950":"650", "980":"680", "985":"685", "995":"695",
}

CASE_CLASS = {
    "600":"C", "610":"D", "620":"D", "630":"D", "640":"A", "650":"A",
    "660":"C", "670":"C", "680":"C", "685":"A", "695":"A", "900":"C",
    "910":"D", "920":"D", "930":"D", "940":"A", "950":"A", "980":"C",
    "985":"A", "995":"A",
}


@dataclass(frozen=True)
class TransferConfiguration:
    name: str
    source_allocation: str


CONFIGURATIONS = (
    TransferConfiguration("F36-like", "native VDI area allocation"),
    TransferConfiguration("F52-like", "Modelica-derived air fraction; non-air remainder projected to AW"),
)


def _base_defaults(case: str) -> dict:
    source = BESTEST / "inputs" / "2_vdi" / ("case900_defaults.json" if case.startswith("9") else "case600_defaults.json")
    return json.loads(source.read_text())


def _construction_registry() -> dict:
    return json.loads(CONSTRUCTION_REGISTRY.read_text())


def _envelope_id(case: str) -> str:
    if case in {"680", "695"}:
        return "680"
    if case in {"980", "995"}:
        return "980"
    return "900" if case.startswith("9") else "600"


def _selected_constructions(case: str) -> dict[str, list[dict]]:
    """Return authoritative outside-to-inside chains for one case."""
    source = _construction_registry()["constructions"]
    envelope = _envelope_id(case)
    if envelope == "600":
        selection = {kind: f"case600 {kind}" for kind in ("wall", "roof", "floor")}
    elif envelope == "680":
        selection = {"wall":"case680 wall", "roof":"case680 roof", "floor":"case600 floor"}
    elif envelope == "900":
        selection = {"wall":"case900 wall", "roof":"case600 roof", "floor":"case900 floor"}
    else:
        selection = {"wall":"case980 wall", "roof":"case680 roof", "floor":"case900 floor"}
    return {
        f"case{envelope} {kind}": deepcopy(source[source_name])
        for kind, source_name in selection.items()
    }


def _glazing_id(case: str) -> str:
    return f"case{case}" if case in {"660", "670"} else "case600"


def _case_changes(case: str) -> list[str]:
    family = "case9xx_deltas.json" if case.startswith("9") else "case6xx_deltas.json"
    return json.loads((BESTEST/"inputs"/family).read_text())["cases"][case]["changes"]


def _configure_defaults(case: str) -> dict:
    d = _base_defaults(case)
    base = case
    shade = 1.0
    window_u, g_value = 3.1, 0.769
    wall_u, roof_u = 0.53, 0.33
    if base in {"610","910"}: shade = 0.84
    if base in {"630","930"}: shade = 0.846*0.915
    glazing = _construction_registry()["glazing_systems"][_glazing_id(case)]
    window_u = float(
        glazing["vdi_whole_window_u_value_w_m2k"]
        if "vdi_whole_window_u_value_w_m2k" in glazing
        else glazing["adapter_u_value_w_m2k"]
    )
    g_value = float(glazing["adapter_g_value"])
    if base in {"680","695","980","995"}: wall_u, roof_u = 0.15, 0.10
    d["u_walls"], d["u_windows"], d["glass_solar_transmittance"] = wall_u, window_u, g_value
    envelope = _envelope_id(case)
    d["constructions"] = _selected_constructions(case)
    d["material_convention"] = {
        "primary": "ashrae140_layers",
        "envelope_case": envelope,
        "dynamic_reduction": "authoritative ASHRAE layer chains",
        "steady_state_transmission": "prescribed component U-values retained separately by the adapter",
        "provenance": _construction_registry()["sources"][f"case{envelope}"],
    }
    d["glazing_convention"] = {
        "id": _glazing_id(case),
        **deepcopy(glazing),
        "provenance": _construction_registry()["sources"].get(_glazing_id(case), [
            "ASHRAE 140-2023 Table 7-10",
            "Buildings/ThermalZones/Detailed/Validation/BESTEST/Data/Win600.mo",
        ]),
    }
    construction = lambda kind: f"case{envelope} {kind}"
    orientations = [("north",0.0,21.6),("east",90.0,16.2),("south",180.0,21.6),("west",270.0,16.2)]
    windows = [("south",180.0,12.0)]
    if base in {"620","630","920","930"}:
        windows = [("west",270.0,6.0),("east",90.0,6.0)]
    window_by_orientation = {name: area for name,_,area in windows}
    d["window_elements"] = [dict(name=f"{name} windows", area_m2=area,
        azimuth_deg=az, tilt_deg=90.0, boundary_condition="Outdoors",
        parent_surface=f"{name} wall", u_value=window_u, g_gl=g_value,
        FF=0.0, F_sh_ob=shade, F_sh_gl=1.0) for name,az,area in windows]
    d["opaque_elements"] = [dict(name=f"{name} wall",
        area_m2=gross-window_by_orientation.get(name,0.0), azimuth_deg=az,
        tilt_deg=90.0, boundary_condition="Outdoors", construction=construction("wall"),
        u_value=wall_u, alpha_s=0.6) for name,az,gross in orientations]
    d["opaque_elements"] += [
        dict(name="roof",area_m2=48.0,azimuth_deg=0.0,tilt_deg=0.0,
             boundary_condition="Outdoors",construction=construction("roof"),u_value=roof_u,alpha_s=0.6),
        dict(name="floor",area_m2=48.0,azimuth_deg=0.0,tilt_deg=180.0,
             boundary_condition="Outdoors",construction=construction("floor"),u_value=0.038,alpha_s=0.6)]
    return d


def case_matrix() -> pd.DataFrame:
    """Return the implementation matrix derived from inspected case definitions."""
    details = {
      "600": ("lightweight base building", "Table 7-2 wall/roof/floor", "south clear double glazing", "none", "0.414 ACH infiltration", "20/27 C", "existing verified Case 600", "Case 600"),
      "610": ("south-window overhang", "none", "base glazing", "south overhang; adapter factor 0.84", "base", "base", "no", "Case 600"),
      "620": ("move 12 m2 glazing to east/west", "none", "6 m2 east + 6 m2 west", "orientation change", "base", "base", "no", "Case 600"),
      "630": ("shade Case 620", "none", "Case 620 glazing", "east/west overhangs and fins", "base", "base", "no", "Case 600"),
      "640": ("heating setback", "none", "base", "none", "base", "10 C night; 07:00-08:00 ramp; 20 C day", "no", "Case 600"),
      "650": ("night ventilation and scheduled cooling", "none", "base", "none", "0.414 ACH + 1409 m3/h 18:00-07:00", "heating off; cooling 07:00-18:00", "no", "Case 600"),
      "660": ("low-e argon glazing", "opaque unchanged; Table 7-17 glazing", "U 1.45; g 0.44", "south unchanged", "base", "base", "new glazing; no opaque layers", "Case 600 opaque"),
      "670": ("clear single-pane glazing", "opaque unchanged; Table 7-21 glazing", "U 7.8; g 0.864", "south unchanged", "base", "base", "new glazing; no opaque layers", "Case 600 opaque"),
      "680": ("increased wall/roof insulation", "Table 7-25 wall and roof; floor unchanged", "base", "none", "base", "base", "new wall and roof", "Case 600 floor only"),
      "685": ("narrow deadband", "none", "base", "none", "base", "19.9/20.1 C", "no", "Case 600"),
      "695": ("Case 680 plus narrow deadband", "Case 680", "base", "none", "base", "19.9/20.1 C", "no additional", "Case 680"),
      "900": ("heavyweight base", "Table 7-27 wall/floor; Case 600 roof", "base", "none", "base", "base", "existing verified Case 900", "Case 900 + Case 600 roof"),
      "910": ("heavyweight south overhang", "none beyond 900", "base", "south overhang; factor 0.84", "base", "base", "no", "Case 900"),
      "920": ("heavyweight east/west windows", "none beyond 900", "6 m2 east + 6 m2 west", "orientation change", "base", "base", "no", "Case 900"),
      "930": ("shade Case 920", "none beyond 900", "Case 920 glazing", "east/west overhangs and fins", "base", "base", "no", "Case 900"),
      "940": ("heavyweight heating setback", "none beyond 900", "base", "none", "base", "same as 640", "no", "Case 900"),
      "950": ("heavyweight night ventilation", "none beyond 900", "base", "none", "same as 650", "same as 650", "no", "Case 900"),
      "980": ("increased heavyweight insulation", "Table 7-31 wall; Case 680 roof; Case 900 floor", "base", "none", "base", "base", "new heavyweight wall", "Case 900 floor + Case 680 roof"),
      "985": ("heavyweight narrow deadband", "none beyond 900", "base", "none", "base", "19.9/20.1 C", "no", "Case 900"),
      "995": ("Case 980 plus narrow deadband", "Case 980", "base", "none", "base", "19.9/20.1 C", "no additional", "Case 980"),
    }
    notebooks = {
      "600":"01_case600_pilot_validation.ipynb", "610":"01a_case610_validation.ipynb",
      "620":"01b_case620_validation.ipynb", "630":"01c_case630_validation.ipynb",
      "640":"01d_case640_validation.ipynb", "650":"01e_case650_validation.ipynb",
      "660":"01f_case660_validation.ipynb", "670":"01g_case670_validation.ipynb",
      "680":"01h_case680_validation.ipynb", "685":"01i_case685_validation.ipynb",
      "695":"01j_case695_validation.ipynb", "900":"02_case900_validation.ipynb",
      "910":"02a_case910_validation.ipynb", "920":"02b_case920_validation.ipynb",
      "930":"02c_case930_validation.ipynb", "940":"02d_case940_validation.ipynb",
      "950":"02e_case950_validation.ipynb", "980":"02f_case980_validation.ipynb",
      "985":"02g_case985_validation.ipynb", "995":"02h_case995_validation.ipynb",
    }
    columns = ("physical_change", "envelope_material_change", "solar_window_change",
               "shading_orientation_change", "infiltration_ventilation_change",
               "thermostat_hvac_change", "new_ashrae_layers_required", "construction_reuse")
    return pd.DataFrame([
        {"case_id":case, "paired_case":CASE_PAIR[case], "parent_base":CASE_PARENT[case],
         **dict(zip(columns, details[case])), "implementation_class":CASE_CLASS[case],
         "iso_notebook":notebooks[case]}
        for case in ALL_CASES
    ])


def distinct_construction_audit() -> pd.DataFrame:
    """Audit every distinct authoritative opaque chain without simulation."""
    registry = _construction_registry()["constructions"]
    rows = []
    for assembly, layers in registry.items():
        rows.append({
            "assembly": assembly,
            "layers_outside_to_inside": " + ".join(x["name"] for x in layers),
            "layer_R_m2K_W": sum(x["thickness_m"] / x["conductivity_w_mk"] for x in layers),
            "layer_C_J_m2K": sum(x["thickness_m"] * x["density_kg_m3"] * x["specific_heat_j_kgk"] for x in layers),
        })
    return pd.DataFrame(rows)


def reduced_construction_audit() -> pd.DataFrame:
    """Reduce the four distinct opaque envelopes without running an hourly case."""
    rows = []
    for case in ("600", "680", "900", "980"):
        defaults = _configure_defaults(case)
        layers = layer_audit(defaults)
        with tempfile.TemporaryDirectory(prefix=f"bestest_{case}_static_") as td:
            default_path = Path(td) / "defaults.json"
            default_path.write_text(json.dumps(defaults))
            rc = RCCase(
                year=2023,
                loc_json=BESTEST / "inputs/2_vdi/case600_location.json",
                geo_json=BESTEST / "inputs/2_vdi/case600_geometry.json",
                default_json=default_path,
                epw_path=WEATHER,
                occupancy_profile_csv=BESTEST / "inputs/2_vdi/case600_occupancy.csv",
                adapter_defaults=VDIAdapterDefaults(
                    inside_total_coefficient_w_m2k=8.0,
                    heating_convective_fraction=1.0,
                    cooling_convective_fraction=1.0,
                    internal_gain_convective_fraction=0.5,
                ),
                use_construction_properties=True,
            )
            outside_r = (
                float(defaults["external_surface_resistance"])
                / rc.adapted.prepared_model.geometry.aw_surface_area_m2
            )
            prepared = prepare_model_case_no_iw_from_prepared(
                rc.adapted.prepared_model,
                inside_total_coefficient_w_m2k=8.0,
                outside_surface_resistance_k_w=outside_r,
            )
        rows.append({
            "envelope_case": case,
            "raw_layer_capacity_J_K": float(layers.total_C_J_K.sum()),
            "VDI_reduced_AW_resistance_K_W": prepared.aw_aggregate.resistance_k_w,
            "VDI_reduced_AW_capacitance_J_K": prepared.aw_aggregate.capacitance_j_k,
        })
    result = pd.DataFrame(rows)
    numeric = result.select_dtypes("number")
    assert np.isfinite(numeric).all().all() and (numeric.to_numpy() > 0).all()
    return result


def validate_case_registry() -> None:
    """Fail before simulation if inheritance, construction, or delta mapping drifts."""
    registry = _construction_registry()
    assert registry["storage_order"].startswith("outside_to_inside")
    assert set(case_matrix().case_id) == set(ALL_CASES)
    assert "B" not in set(CASE_CLASS.values())
    for case in ALL_CASES:
        configured = _configure_defaults(case)
        assert set(configured["constructions"]) == {
            f"case{_envelope_id(case)} wall",
            f"case{_envelope_id(case)} roof",
            f"case{_envelope_id(case)} floor",
        }
        assert sum(x["area_m2"] for x in configured["window_elements"]) == 12.0
        # The VDI adapter removes its prescribed inside/outside films from the
        # whole-window U-value.  Every registry value must therefore leave a
        # positive film-excluded construction resistance.
        window_r = 1.0 / configured["u_windows"] - 1.0 / 8.0 - 1.0 / 25.0
        assert window_r > 0.0, (case, configured["u_windows"], window_r)
    for case in ("680", "695"):
        selected = _selected_constructions(case)
        assert selected["case680 floor"] == registry["constructions"]["case600 floor"]
    for case in ("900", "910", "920", "930", "940", "950", "985"):
        selected = _selected_constructions(case)
        assert selected["case900 roof"] == registry["constructions"]["case600 roof"]
    for case in ("980", "995"):
        selected = _selected_constructions(case)
        assert selected["case980 roof"] == registry["constructions"]["case680 roof"]
        assert selected["case980 floor"] == registry["constructions"]["case900 floor"]
    audit = distinct_construction_audit()
    assert np.isfinite(audit[["layer_R_m2K_W", "layer_C_J_m2K"]]).all().all()
    assert (audit[["layer_R_m2K_W", "layer_C_J_m2K"]].to_numpy() > 0).all()


def _schedules(case: str):
    hod = INDEX.hour.to_numpy()
    heat = np.full(8760, 20.0); cool = np.full(8760, 27.0)
    heat_on = np.ones(8760, dtype=bool); cool_on = np.ones(8760, dtype=bool)
    if case in {"640","940"}:
        heat = np.where((hod < 7)|(hod >= 23), 10.0, 20.0)
        heat[hod == 7] = 10.0
    if case in {"650","950"}:
        heat_on[:] = False
        cool_on = (hod >= 7) & (hod < 18)
    if case in {"685","695","985","995"}:
        heat[:], cool[:] = 19.9, 20.1
    return heat, cool, heat_on, cool_on


def _neutralize_longwave(boundary):
    t_k = boundary.radiation.outdoor_air_temperature_c + 273.15
    lw = 0.93*5.670374419e-8*t_k**4
    return replace(boundary, radiation=replace(boundary.radiation,
        atmospheric_radiation_w_m2=lw, ground_radiation_w_m2=lw))


def _transform(configuration: TransferConfiguration, window_u: float, solar_trace: list[float], case: str):
    f_air = window_u*12.0/(9.1*171.6) if configuration.name == "F52-like" else 0.0
    def apply(position, hourly):
        sources = hourly.exterior_radiant_sources
        native = math.fsum(x.radiant_source_w for x in sources)
        solar_trace.append(native)
        convective = hourly.internal_convective_gain_w
        if f_air:
            convective += f_air*native
            sources = tuple(replace(x, radiant_source_w=(1-f_air)*x.radiant_source_w) for x in sources)
        flow = 0.414*VOLUME/3600.0
        if case in {"650","950"} and (INDEX[position].hour >= 18 or INDEX[position].hour < 7):
            flow += 1409.0/3600.0
        resistance = 1.0/(RHO*CP*flow)
        return replace(hourly,
            boundary_inputs=tuple(_neutralize_longwave(x) for x in hourly.boundary_inputs),
            exterior_radiant_sources=sources,
            internal_convective_gain_w=convective,
            ventilation_resistance_k_w=resistance)
    return apply


def simulate_case(case: str, configuration: TransferConfiguration):
    if case not in ALL_CASES: raise ValueError(case)
    defaults = _configure_defaults(case)
    heat, cool, heat_on, cool_on = _schedules(case)
    solar_trace: list[float] = []
    with tempfile.TemporaryDirectory(prefix=f"bestest_{case}_") as td:
        default_path = Path(td)/"defaults.json"
        default_path.write_text(json.dumps(defaults))
        rc = RCCase(year=2023, loc_json=VDI/"inputs/case600_location.json",
            geo_json=VDI/"inputs/case600_geometry.json", default_json=default_path,
            epw_path=WEATHER, occupancy_profile_csv=VDI/"inputs/case600_occupancy.csv",
            adapter_defaults=VDIAdapterDefaults(inside_total_coefficient_w_m2k=8.0,
                heating_convective_fraction=1.0, cooling_convective_fraction=1.0,
                internal_gain_convective_fraction=0.5),
            use_construction_properties=True)
        sim = run_thermostat_case_no_iw(rc, index=INDEX, gains_w=200.0,
            occupancy_fraction=ONES, heating_setpoint_schedule=heat,
            cooling_setpoint_schedule=cool, heating_availability_schedule=heat_on,
            cooling_availability_schedule=cool_on, ventilation_fraction_schedule=ZEROS,
            heat_recovery_efficiency_schedule=ZEROS,
            hourly_input_transform=_transform(configuration, defaults["u_windows"], solar_trace, case))
    assert len(solar_trace) == 8760 and np.isfinite(solar_trace).all()
    return sim, np.asarray(solar_trace), defaults


def _metric_row(case, configuration, sim, solar):
    load = np.asarray([r.total_hvac_load_w for r in sim.hourly_results])
    assert load.shape == (8760,) and np.isfinite(load).all()
    assert solar.shape == (8760,) and np.isfinite(solar).all()
    return dict(case=case, configuration=configuration.name,
        source_allocation=configuration.source_allocation,
        heating_MWh=np.clip(load,0,None).sum()/1e6,
        cooling_MWh=np.clip(-load,0,None).sum()/1e6,
        annual_transmitted_solar_MWh=solar.sum()/1e6,
        maximum_balance_residual_W=sim.maximum_absolute_balance_residual_w), load


def layer_audit(defaults: dict) -> pd.DataFrame:
    areas = {"wall":63.6,"roof":48.0,"floor":48.0}
    rows=[]
    for name,layers in defaults["constructions"].items():
        kind=next(x for x in areas if name.endswith(x)); area=areas[kind]
        r=sum(x["thickness_m"]/x["conductivity_w_mk"] for x in layers)
        c=sum(x["thickness_m"]*x["density_kg_m3"]*x["specific_heat_j_kgk"] for x in layers)
        rows.append(dict(assembly=kind,area_m2=area,layer_R_m2K_W=r,
                         layer_C_J_m2K=c,total_C_J_K=area*c))
    return pd.DataFrame(rows)


def construction_traceability(defaults: dict) -> pd.DataFrame:
    """Summarize the primary Case 900 layers and their VDI AW reduction."""
    layers = layer_audit(defaults)
    with tempfile.TemporaryDirectory(prefix="bestest_900_trace_") as td:
        default_path = Path(td) / "defaults.json"
        default_path.write_text(json.dumps(defaults))
        rc = RCCase(
            year=2023,
            loc_json=BESTEST / "inputs/2_vdi/case600_location.json",
            geo_json=BESTEST / "inputs/2_vdi/case600_geometry.json",
            default_json=default_path,
            epw_path=WEATHER,
            occupancy_profile_csv=BESTEST / "inputs/2_vdi/case600_occupancy.csv",
            adapter_defaults=VDIAdapterDefaults(
                inside_total_coefficient_w_m2k=8.0,
                heating_convective_fraction=1.0,
                cooling_convective_fraction=1.0,
                internal_gain_convective_fraction=0.5,
            ),
            use_construction_properties=True,
        )
        outside_r = (
            float(defaults["external_surface_resistance"])
            / rc.adapted.prepared_model.geometry.aw_surface_area_m2
        )
        prepared = prepare_model_case_no_iw_from_prepared(
            rc.adapted.prepared_model,
            inside_total_coefficient_w_m2k=8.0,
            outside_surface_resistance_k_w=outside_r,
        )
    layer_names = {
        name.rsplit(" ", 1)[-1]: " + ".join(layer["name"] for layer in chain)
        for name, chain in defaults["constructions"].items()
    }
    raw_capacity = float(layers.total_C_J_K.sum())
    values = np.asarray([
        raw_capacity,
        prepared.aw_aggregate.resistance_k_w,
        prepared.aw_aggregate.capacitance_j_k,
    ])
    assert np.isfinite(values).all() and (values > 0).all()
    return pd.DataFrame([{
        "construction_convention": defaults["material_convention"]["primary"],
        "wall_layers": layer_names["wall"],
        "floor_layers": layer_names["floor"],
        "roof_layers": layer_names["roof"],
        "raw_layer_capacity_J_K": raw_capacity,
        "VDI_reduced_AW_resistance_K_W": prepared.aw_aggregate.resistance_k_w,
        "VDI_reduced_AW_capacitance_J_K": prepared.aw_aggregate.capacitance_j_k,
    }])


def case900_input_audit() -> pd.DataFrame:
    return pd.DataFrame([
      ("geometry","48 m2; 129.6 m3; same surfaces","unchanged from Case 600","inputs/case900.json"),
      ("construction layers","ASHRAE 140 Case 900 wall/floor; Case 600 roof","benchmark-prescribed change","ASHRAE 140 Table 7-27; detailed Modelica records"),
      ("prescribed U-values","wall .53; roof .33; floor .038 W/m2K","unchanged from Case 600","inputs/case900.json"),
      ("thermal mass/capacitance","layer-derived by VDI dynamic reduction","benchmark-prescribed change","verified physical layer chains"),
      ("effective mass area","2.43 x 48 = 116.64 m2; recorded, not applied","unresolved provenance","no direct no-IW VDI mapping"),
      ("glazing","12 m2 south; U 3.1; g .769","unchanged from Case 600","inputs/case900.json"),
      ("infiltration/ventilation","0.414 1/h; no mechanical ventilation","unchanged from Case 600","repository comparator; canonical provenance open"),
      ("internal gains","200 W; 50% air/50% AW","implementation assumption","comparator-consistent no-IW projection"),
      ("solar properties","native VDI; absorptance .6; g .769","unchanged from Case 600","candidate implementation"),
      ("setpoints/control","20/27 C; ideal air HVAC","unchanged from Case 600","benchmark/comparator"),
      ("schedules","constant annual availability","unchanged from Case 600","benchmark"),
      ("exterior boundary","long-wave harmonised to outdoor dry bulb","implementation assumption","Case600 carry-forward")],
      columns=["item","current_setting","classification","source_provenance"])


def checklist(case="900") -> pd.DataFrame:
    settings = ["no-IW","F36/F52 variants","ASHRAE 140 layers; prescribed U-values retained","total h_i=8 W/m2K",
                "harmonised","50% air / 50% AW","0.414 1/h","benchmark geometry/schedules/controls"]
    sources = ["Case600 candidate","Case600 candidate","ASHRAE 140 Table 7-27 + detailed Modelica records","VDI-side convention",
               "Case600 candidate","comparator projection","repository comparator; canonical source open","canonical case record"]
    categories=["IW topology","Solar/source allocation","Envelope convention","Inside heat-transfer treatment",
                "Exterior long-wave treatment","Internal-gain allocation","Airflow/infiltration provenance","Geometry, schedules and controls"]
    questions=["Is the intended topology present and are absent-IW consequences explicit?",
      "Which nodes receive solar and is allocation native, derived, or projected?",
      "Which inputs control transmission and dynamics, and are they reconciled?",
      "Which total convention is active and how is it split?",
      "Is long-wave native or harmonised and what is replaced?",
      "Which nodes receive gains and what is the source of the split?",
      "What airflow quantity and provenance are used, and is conversion applied once?",
      "Do geometry, schedules, setpoints, availability, and control match the case?"]
    return pd.DataFrame(dict(case=case,category=categories,verification_question=questions,
                             current_setting=settings,source_provenance=sources))


def _distance(value, bounds):
    lo,hi=bounds
    return max(lo-value,0.0,value-hi)


def run_case900(output: Path | None = None):
    output = output or BESTEST/"results/2_vdi/case900_vdi_transfer_ashrae140_layers"; output.mkdir(parents=True,exist_ok=True)
    defaults=_configure_defaults("900"); layers=layer_audit(defaults)
    traceability=construction_traceability(defaults)
    assert math.isclose(layers.total_C_J_K.sum(),15479951.712,rel_tol=0,abs_tol=1e-6)
    rows=[]; hourly=[]
    for cfg in CONFIGURATIONS:
        sim,solar,_=simulate_case("900",cfg); row,load=_metric_row("900",cfg,sim,solar)
        row.update(heating_lower=HEAT_BOUNDS_900[0],heating_upper=HEAT_BOUNDS_900[1],
                   cooling_lower=COOL_BOUNDS_900[0],cooling_upper=COOL_BOUNDS_900[1])
        row["heating_in_range"]=HEAT_BOUNDS_900[0]<=row["heating_MWh"]<=HEAT_BOUNDS_900[1]
        row["cooling_in_range"]=COOL_BOUNDS_900[0]<=row["cooling_MWh"]<=COOL_BOUNDS_900[1]
        row["both_in_range"]=row["heating_in_range"] and row["cooling_in_range"]
        row["D_MWh_norm"]=math.hypot(_distance(row["heating_MWh"],HEAT_BOUNDS_900)/1.24,
                                      _distance(row["cooling_MWh"],COOL_BOUNDS_900)/.25)
        rows.append(row)
        hourly.extend(dict(timestamp=t,case="900",configuration=cfg.name,
                           native_transmitted_solar_W=s,HVAC_load_W=q,
                           heating_load_W=max(q,0),cooling_load_W=max(-q,0))
                      for t,s,q in zip(INDEX,solar,load))
    summary=pd.DataFrame(rows)
    summary=summary[["configuration","heating_MWh","cooling_MWh",
        "heating_in_range","cooling_in_range","both_in_range","D_MWh_norm",
        "maximum_balance_residual_W"]]
    hourly=pd.DataFrame(hourly)
    assert np.isfinite(summary.select_dtypes("number")).all().all()
    assert summary.maximum_balance_residual_W.max()<=1e-9
    summary.to_csv(output/"case900_vdi_transfer_summary.csv",index=False)
    hourly.to_csv(output/"case900_vdi_transfer_hourly.csv",index=False)
    case900_input_audit().to_csv(output/"case900_input_translation_audit.csv",index=False)
    layers.to_csv(output/"case900_layer_capacity_audit.csv",index=False)
    traceability.to_csv(output/"case900_construction_traceability.csv",index=False)
    checklist().to_csv(output/"case900_eight_point_checklist.csv",index=False)
    pd.DataFrame({"required_file":["case900_vdi_transfer_summary.csv","case900_vdi_transfer_hourly.csv",
      "case900_input_translation_audit.csv","case900_layer_capacity_audit.csv",
      "case900_construction_traceability.csv","case900_eight_point_checklist.csv"]}).to_csv(output/"manifest.csv",index=False)
    return summary,hourly,layers,traceability


def verify_case600_replay(tolerance=1e-9):
    expected=pd.read_csv(CASE600_RESULTS).set_index("factorial_id")
    rows=[]
    for cfg,fid in zip(CONFIGURATIONS,("F36","F52")):
        sim,solar,_=simulate_case("600",cfg); row,_=_metric_row("600",cfg,sim,solar)
        row.update(factorial_id=fid,
            expected_heating_MWh=expected.at[fid,"heating_MWh"],expected_cooling_MWh=expected.at[fid,"cooling_MWh"])
        row["heating_difference_MWh"]=row["heating_MWh"]-row["expected_heating_MWh"]
        row["cooling_difference_MWh"]=row["cooling_MWh"]-row["expected_cooling_MWh"]
        rows.append(row)
    result=pd.DataFrame(rows)
    assert result[["heating_difference_MWh","cooling_difference_MWh"]].abs().to_numpy().max()<=tolerance
    return result


def _reference_table(section):
    lines=REFERENCE.read_text().splitlines(); start=next(i for i,x in enumerate(lines) if x.startswith("# ") and x.endswith(section))
    table=[]
    for line in lines[start+1:]:
        if line.startswith("# "): break
        if line.startswith("|"):
            cells=[x.strip() for x in line.strip().strip("|").split("|")]
            if not all(set(x)<={"-",":"} for x in cells): table.append(cells)
    return pd.DataFrame(table[1:],columns=table[0])


def reference_bounds():
    rows=[]
    for metric,section in (("heating","Annual heating energy reference data"),("cooling","Annual cooling energy reference data")):
        t=_reference_table(section)
        for _,r in t.iterrows(): rows.append(dict(case=str(r.Case),metric=metric,lower=float(r.Lower),upper=float(r.Upper)))
    return pd.DataFrame(rows)


def apply_bounds(results):
    bounds=reference_bounds(); out=results.merge(bounds.pivot(index="case",columns="metric",values=["lower","upper"]).pipe(
        lambda x: x.set_axis([f"{a}_{b}" for a,b in x.columns],axis=1)).reset_index(),on="case")
    flags=[]
    for _,r in out.iterrows():
        valid=r.lower_cooling<=r.upper_cooling and r.lower_heating<=r.upper_heating
        hp=r.lower_heating<=r.heating_MWh<=r.upper_heating if valid else None
        cp=r.lower_cooling<=r.cooling_MWh<=r.upper_cooling if valid else None
        if not valid: dist=np.nan
        elif r.upper_heating==r.lower_heating and not math.isclose(r.heating_MWh,r.lower_heating,abs_tol=1e-9): dist=np.nan
        else:
            dh=0 if r.upper_heating==r.lower_heating else _distance(r.heating_MWh,(r.lower_heating,r.upper_heating))/(r.upper_heating-r.lower_heating)
            dc=_distance(r.cooling_MWh,(r.lower_cooling,r.upper_cooling))/(r.upper_cooling-r.lower_cooling)
            dist=math.hypot(dh,dc)
        flags.append((valid,hp,cp,(hp and cp) if valid else None,dist))
    out[["bounds_valid","heating_in_range","cooling_in_range","both_in_range","D_MWh_norm"]]=flags
    return out


def run_sequence(configurations, output: Path | None = None):
    output=output or BESTEST/"results/2_vdi/bestest_6xx_9xx_ashrae140_layers"; output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for case in ALL_CASES:
        for cfg in configurations:
            sim,solar,_=simulate_case(case,cfg); row,_=_metric_row(case,cfg,sim,solar); rows.append(row)
    annual=apply_bounds(pd.DataFrame(rows)); annual.to_csv(output/"annual_results.csv",index=False)
    patterns=response_patterns(annual); patterns.to_csv(output/"response_patterns.csv",index=False)
    mass=mass_pair_patterns(annual); mass.to_csv(output/"lightweight_heavyweight_pairs.csv",index=False)
    checks=pd.concat([checklist(case) for case in ALL_CASES],ignore_index=True); checks.to_csv(output/"eight_point_checklists.csv",index=False)
    pd.DataFrame({"required_file":["annual_results.csv","response_patterns.csv","lightweight_heavyweight_pairs.csv","eight_point_checklists.csv"]}).to_csv(output/"manifest.csv",index=False)
    return annual,patterns,mass


def response_patterns(annual):
    programs=["BSIMAC","CSE","DeST","EnergyPlus","ESP-r","TRNSYS","Modelica ISO13790"]
    refs={m:_reference_table(s).set_index("Case") for m,s in (("heating","Annual heating energy reference data"),("cooling","Annual cooling energy reference data"))}
    rows=[]
    for _,r in annual.iterrows():
        base="900" if str(r.case).startswith("9") else "600"
        for metric in ("heating","cooling"):
            v=float(r[f"{metric}_MWh"]); b=float(annual[(annual.case==base)&(annual.configuration==r.configuration)][f"{metric}_MWh"].iloc[0]); delta=v-b
            rd=np.array([float(refs[metric].at[str(r.case),p])-float(refs[metric].at[base,p]) for p in programs])
            median=float(np.median(rd)); direction=(np.sign(delta)==np.sign(median)) or (abs(delta)<1e-12 and abs(median)<1e-12)
            rows.append(dict(case=r.case,configuration=r.configuration,metric=metric,base_case=base,
                vdi_delta_MWh=delta,reference_delta_min_MWh=rd.min(),reference_delta_median_MWh=median,
                reference_delta_max_MWh=rd.max(),majority_direction_matches=direction,
                within_reference_delta_envelope=rd.min()<=delta<=rd.max()))
    return pd.DataFrame(rows)


def mass_pair_patterns(annual):
    rows=[]
    for light,heavy in {"600":"900",**PAIR_MAP}.items():
        for cfg in annual.configuration.unique():
            for metric in ("heating","cooling"):
                a=annual[(annual.case==light)&(annual.configuration==cfg)][f"{metric}_MWh"].iloc[0]
                b=annual[(annual.case==heavy)&(annual.configuration==cfg)][f"{metric}_MWh"].iloc[0]
                rows.append(dict(lightweight_case=light,heavyweight_case=heavy,configuration=cfg,
                                 metric=metric,heavy_minus_light_MWh=b-a))
    return pd.DataFrame(rows)
