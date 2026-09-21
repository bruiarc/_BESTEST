"""Reproducible BESTEST registry, execution tracks and validation summaries.

This module is deliberately the only new 20-case implementation layer.  It
uses the existing Modelica runner and RClib ``Zone`` rather than replicating
their internals in notebooks.  ``matched_modelica`` always denotes the
Modelica-resolved net zone solar forcing (``zonHVAC.solGai.y`` in W); native
solar is intentionally a separately labelled input path.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd

from .dependencies import VALIDATION_ROOT, radiation_classes, zone_class

CONDITIONED_CASES = ("600", "610", "620", "630", "640", "650", "660", "670", "680", "685", "695", "900", "910", "920", "930", "940", "950", "980", "985", "995")
FREE_FLOATING_CASES = ("600FF", "650FF", "680FF", "900FF", "950FF")
ALL_CASES = CONDITIONED_CASES + FREE_FLOATING_CASES
EXPECTED_FIGURES = (
    "annual_heating.png", "annual_cooling.png", "peak_heating.png", "peak_cooling.png",
    "hourly_load_600_Jan4.png", "hourly_load_900_Jan4.png", "max_temperature.png",
    "min_temperature.png", "FF_temperature_600FF_Feb1.png", "FF_temperature_900FF_Feb1.png",
    "FF_temperature_650FF_Jul14.png", "FF_temperature_950FF_Jul14.png",
    "ave_temperature.png", "bin_temperature_900FF.png",
)


@dataclass(frozen=True)
class CaseDefinition:
    case: str
    modelica_class: str
    free_floating: bool
    mass: str
    mass_capacity_j_m2k: float
    mass_area_factor: float
    window_areas_m2: tuple[float, float, float, float]  # north, west, south, east
    window_u_w_m2k: float = 3.1
    g_value: float = .769
    wall_u_w_m2k: float = .53
    roof_u_w_m2k: float = .33
    floor_u_w_m2k: float = .038
    shading_factor: float = 1.0
    heating: str = "20C always"
    cooling: str = "27C always"
    ventilation: str = "0.414 ACH infiltration"

def _definition(case: str, *, ff: bool = False) -> CaseDefinition:
    heavy = case.startswith("9")
    family = "Cases9xx" if heavy else "Cases6xx"
    mass, cap, fac = ("heavyweight", 307750., 2.43) if heavy else ("lightweight", 42167., 2.95)
    windows = (0., 0., 12., 0.)
    wall, roof, uwin, g, shade = .53, .33, 3.1, .769, 1.
    heating, cooling, ventilation = "20C always", "27C always", "0.414 ACH infiltration"
    if ff:
        # The published free-floating source retains pre-2020 U/g rounding.
        wall, roof, g = .534, .327, .789
        heating = cooling = "off"
    base = case[:-2] if ff else case
    if base in {"610", "910"}: shade = .84
    if base in {"620", "630", "920", "930"}: windows = (0., 6., 0., 6.)
    if base in {"630", "930"}: shade = .846 * .915
    if base in {"640", "940"}: heating = "10C 23:00-07:00; ramp 07:00-08:00; 20C 08:00-23:00"
    if base in {"650", "950"}:
        heating = "off"; cooling = "27C 07:00-18:00 only"
        ventilation = "0.414 ACH + 1409 m3/h 18:00-07:00"
    if base == "660": uwin, g = 1.45, .44
    if base == "670": uwin, g = 7.8, .864
    if base in {"680", "695", "980", "995"}: wall, roof = .15, .1
    if base in {"685", "695", "985", "995"}: heating, cooling = "19.9C always", "20.1C always"
    cls = f"Buildings.ThermalZones.ISO13790.Validation.BESTEST.{family}.Case{case}"
    return CaseDefinition(case, cls, ff, mass, cap, fac, windows, uwin, g, wall, roof, .0377 if ff else .038, shade, heating, cooling, ventilation)


CASE_DEFINITIONS = {case: _definition(case, ff=case.endswith("FF")) for case in ALL_CASES}


def _setpoints(definition: CaseDefinition, hour: int) -> tuple[float, float, bool, bool]:
    hod = hour % 24
    hea, coo, hea_on, coo_on = 20., 27., True, True
    if definition.free_floating: return -1e6, 1e6, False, False
    if "19.9" in definition.heating: hea, coo = 19.9, 20.1
    if "10C" in definition.heating:
        hea = 10. if hod < 7 or hod >= 23 else 20. if hod >= 8 else 10. + 10. * (hod - 7)
    if definition.heating == "off": hea_on = False
    if "07:00-18:00" in definition.cooling: coo_on = 7 <= hod < 18
    return hea, coo, hea_on, coo_on


def make_rclib_zone(definition: CaseDefinition):
    """Map explicitly common BESTEST inputs into the RClib 5R1C interface."""
    Zone = zone_class()
    opaque_area = 159.6
    h_opaque = definition.wall_u_w_m2k * 63.6 + definition.roof_u_w_m2k * 48 + definition.floor_u_w_m2k * 48
    zone = Zone(window_area=12., walls_area=opaque_area, floor_area=48., room_vol=129.6,
        total_internal_area=171.6, u_windows=definition.window_u_w_m2k,
        u_walls=h_opaque / opaque_area, ach_vent=.414, ach_infl=0., ventilation_efficiency=0.,
        thermal_capacitance_per_floor_area=definition.mass_capacity_j_m2k,
        effective_mass_area_per_floor_area=definition.mass_area_factor,
        t_set_heating=20., t_set_cooling=27.)
    zone.h_tr_is = 2.1 * 171.6
    zone.h_ve_adj = 1200. * .414 * 129.6 / 3600.
    return zone


def hourly_modelica_forcing(modelica: pd.DataFrame) -> pd.DataFrame:
    """Return exactly 8760 completed-hour timestamps; reject shifts/gaps."""
    time = np.arange(3600., 31536001., 3600.)
    required = ("time", "zonHVAC.solGai.y", "weaDat.weaBus.TDryBul", "zonHVAC.TAir")
    missing = set(required).difference(modelica.columns)
    if missing: raise ValueError(f"missing Modelica forcing columns: {sorted(missing)}")
    value = lambda col: np.interp(time, modelica.time, modelica[col].astype(float))
    out = pd.DataFrame({"time_s": time, "modelica_resolved_solar_gain_w": value("zonHVAC.solGai.y"),
        "outdoor_temperature_c": value("weaDat.weaBus.TDryBul") - 273.15,
        "modelica_air_temperature_c": value("zonHVAC.TAir") - 273.15})
    if len(out) != 8760 or not np.isfinite(out.to_numpy(float)).all(): raise ValueError("forcing must be finite 8760-hour data")
    return out


def run_rclib_matched_forcing(definition: CaseDefinition, modelica: pd.DataFrame) -> pd.DataFrame:
    """Modelica-resolved solar forcing supplied to the RClib thermal model."""
    forcing, zone = hourly_modelica_forcing(modelica), make_rclib_zone(definition)
    mass = air = 20.; rows = []
    for hour, row in enumerate(forcing.itertuples(index=False)):
        hea, coo, hea_on, coo_on = _setpoints(definition, hour)
        zone.t_set_heating, zone.t_set_cooling = hea, coo
        if "1409" in definition.ventilation and (hour % 24 >= 18 or hour % 24 < 7):
            zone.h_ve_adj = 1200 * (.414 * 129.6 / 3600 + 1409 / 3600)
        else: zone.h_ve_adj = 1200 * .414 * 129.6 / 3600
        zone.solve_energy(200., float(row.modelica_resolved_solar_gain_w), float(row.outdoor_temperature_c), mass, air, heating_available=hea_on)
        mass, air = zone.t_m_next, zone.t_air
        rows.append((row.time_s, air, max(zone.heating_demand, 0.) if hea_on else 0., max(-zone.cooling_demand, 0.) if coo_on else 0., hea, coo, hea_on, coo_on))
    result = pd.DataFrame(rows, columns=("time_s", "rclib_air_temperature_c", "rclib_heating_w", "rclib_cooling_w", "heating_setpoint_c", "cooling_setpoint_c", "heating_available", "cooling_available"))
    return forcing.merge(result, on="time_s").assign(solar_mode="matched_modelica")


def _denver_epw() -> Path:
    """Resolve the same Denver TMY3 EPW used by the Buildings weather reader."""
    names = (VALIDATION_ROOT / "modelica-buildings", VALIDATION_ROOT / "modelica-buildings-github-master")
    for root in names:
        candidate = root / "Buildings/Resources/weatherdata/USA_CO_Denver.Intl.AP.725650_TMY3.epw"
        if candidate.is_file(): return candidate
    raise FileNotFoundError("Denver TMY3 EPW not available beside either Buildings checkout")


def run_rclib_native_solar(definition: CaseDefinition, modelica: pd.DataFrame, epw: Path | None = None) -> pd.DataFrame:
    """Run RClib's own radiation pathway; never consumes Modelica solar values.

    The common case definition supplies geometry, U-values and optical data.
    Simple BESTEST shading is retained as its documented ISO reduction factor;
    this is a native RClib solar calculation, not an attempt to re-create the
    Modelica sky/radiation preprocessing.
    """
    Location, Window, OpaqueSurface = radiation_classes()
    weather = Location(epwfile_path=epw or _denver_epw())
    if len(weather.weather_data) != 8760: raise ValueError("native solar requires a complete 8760-hour EPW")
    sky = dict(external_surface_resistance=.04, external_radiative_coefficient=4.5, sky_air_temperature_difference=11.)
    azimuth = (180., -90., 0., 90.)
    windows = [Window(azimuth_tilt=azimuth[i], alititude_tilt=90., area=area,
        glass_solar_transmittance=definition.g_value, frame_fraction=.001,
        u_value=definition.window_u_w_m2k, sky_view_factor=.5, **sky)
        for i, area in enumerate(definition.window_areas_m2) if area]
    walls = [OpaqueSurface(azimuth_tilt=a, alititude_tilt=90., area=area,
        u_value=definition.wall_u_w_m2k, solar_absorptivity=.6, sky_view_factor=.5, **sky)
        for area, a in zip((21.6, 16.2, 9.6, 16.2), azimuth)]
    roof = OpaqueSurface(azimuth_tilt=0., alititude_tilt=0., area=48.,
        u_value=definition.roof_u_w_m2k, solar_absorptivity=.6, sky_view_factor=1., **sky)
    zone, mass, air, rows = make_rclib_zone(definition), 20., 20., []
    modelica_forcing = hourly_modelica_forcing(modelica)
    for hour, (_, weather_row) in enumerate(weather.weather_data.iterrows()):
        altitude, direction = weather.calc_sun_position(39.83, -104.65, 1995, hour)
        dni, dhi = float(weather_row.dirnorrad_Whm2), float(weather_row.difhorrad_Whm2)
        for surface in windows + walls + [roof]: surface.calc_solar_gains(altitude, direction, dni, dhi)
        solar = definition.shading_factor * sum(x.solar_gains for x in windows) + sum(x.solar_gains for x in walls + [roof])
        hea, coo, hea_on, coo_on = _setpoints(definition, hour)
        zone.t_set_heating, zone.t_set_cooling = hea, coo
        zone.h_ve_adj = 1200 * (.414 * 129.6 / 3600 + (1409 / 3600 if "1409" in definition.ventilation and (hour % 24 >= 18 or hour % 24 < 7) else 0))
        zone.solve_energy(200., float(solar), float(weather_row.drybulb_C), mass, air, heating_available=hea_on)
        mass, air = zone.t_m_next, zone.t_air
        rows.append((float((hour + 1) * 3600), air, solar, max(zone.heating_demand, 0.) if hea_on else 0., max(-zone.cooling_demand, 0.) if coo_on else 0., hea, coo, hea_on, coo_on))
    native = pd.DataFrame(rows, columns=("time_s", "rclib_air_temperature_c", "native_rclib_solar_gain_w", "rclib_heating_w", "rclib_cooling_w", "heating_setpoint_c", "cooling_setpoint_c", "heating_available", "cooling_available"))
    return modelica_forcing.merge(native, on="time_s").assign(solar_mode="native_rclib")


def annual_metrics(track: pd.DataFrame, definition: CaseDefinition, *, source: str) -> pd.DataFrame:
    """Annual integrations, peaks and FF temperatures using explicit signs/units."""
    out: list[dict[str, object]] = []
    if definition.free_floating:
        series = track["rclib_air_temperature_c"] if source == "RClib" else track["modelica_air_temperature_c"]
        for metric, value, index, unit in (("maximum_free_floating_temperature", series.max(), series.idxmax(), "degC"), ("minimum_free_floating_temperature", series.min(), series.idxmin(), "degC"), ("annual_mean_free_floating_temperature", series.mean(), None, "degC")):
            out.append({"case": definition.case, "metric": metric, "value": value, "unit": unit, "occurrence_time_s": float(track.time_s.iloc[index]) if index is not None else np.nan, "result_source": source})
    else:
        prefix = "rclib" if source == "RClib" else "modelica"
        for metric, col in (("annual_heating_energy", f"{prefix}_heating_w"), ("annual_cooling_energy", f"{prefix}_cooling_w")):
            if col in track: out.append({"case": definition.case, "metric": metric, "value": track[col].sum() / 1e6, "unit": "MWh", "occurrence_time_s": np.nan, "result_source": source})
        for metric, col in (("peak_heating_load", f"{prefix}_heating_w"), ("peak_cooling_load", f"{prefix}_cooling_w")):
            if col in track:
                index = track[col].idxmax(); out.append({"case": definition.case, "metric": metric, "value": track.loc[index, col] / 1000, "unit": "kW", "occurrence_time_s": track.loc[index, "time_s"], "result_source": source})
    return pd.DataFrame(out)


def modelica_track(modelica: pd.DataFrame) -> pd.DataFrame:
    out = hourly_modelica_forcing(modelica)
    val = lambda column: np.interp(out.time_s, modelica.time, modelica[column].astype(float)) if column in modelica else np.zeros(len(out))
    out["modelica_heating_w"] = val("PHea.y")
    out["modelica_cooling_w"] = -val("PCoo.y")
    return out


class _TableParser(HTMLParser):
    def __init__(self): super().__init__(); self.tables=[]; self.table=None; self.row=None
    def handle_starttag(self, tag, attrs):
        if tag == "table": self.table=[]
        elif tag == "tr" and self.table is not None: self.row=[]
        elif tag in {"td", "th"} and self.row is not None: self.cell=[]
    def handle_data(self, data):
        if hasattr(self, "cell"): self.cell.append(data.strip())
    def handle_endtag(self, tag):
        if tag in {"td", "th"} and hasattr(self, "cell"): self.row.append(" ".join(x for x in self.cell if x)); del self.cell
        elif tag == "tr" and self.row is not None: self.table.append(self.row); self.row=None
        elif tag == "table" and self.table is not None: self.tables.append(self.table); self.table=None


def published_reference_tables(usersguide: Path | None = None) -> pd.DataFrame:
    """Programmatically read the authoritative tables bundled with Buildings."""
    path = usersguide or VALIDATION_ROOT / "modelica-buildings" / "Buildings" / "ThermalZones" / "ISO13790" / "Validation" / "BESTEST" / "UsersGuide.mo"
    parser = _TableParser(); parser.feed(path.read_text(encoding="utf-8"))
    rows=[]
    for table in parser.tables:
        metric = header = None
        for r in table:
            if r and "Annual heating load" in r[0]: metric = "annual_heating_energy"; header = None
            elif r and "Annual cooling load" in r[0]: metric = "annual_cooling_energy"; header = None
            elif r and r[0] == "Case": header = r
            elif metric and header and len(r) == len(header) and r[0].startswith("Case"):
                data=dict(zip(header, r)); rows.append({"case": data["Case"].replace("Case", ""), "metric": metric, "lower": float(data["Lower limit"]), "upper": float(data["Upper limit"]), "modelica_iso13790_published": float(data["ISO13790"]), "reference_program_mean": np.mean([float(data[x]) for x in ("BSIMAC", "CSE", "DeST", "EnergyPlus", "ESP-r", "TRNSYS")] )})
    return pd.DataFrame(rows)

