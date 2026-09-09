"""Build the reproducible Case 600 VDI 6007 audit notebook and report."""

from pathlib import Path
import csv
import json

HERE = Path(__file__).resolve().parent

ROWS = [
    ("Location / weather station", "X", "", "RCCase.epw_path; solar weather_location", "Denver TMY3 / 39.83 deg N, -104.65 deg E"),
    ("Simulation year and calendar", "X", "", "RCCase.year; hourly index", "2023 surrogate non-leap year; 8760 h"),
    ("Timestep", "X", "", "RCCase.timestep_hours", "1 h"),
    ("Floor area", "X", "", "RoomGeometry.floor_area_m2", "48.0 m2"),
    ("Room volume", "X", "", "RoomGeometry.volume_m3", "129.6 m3"),
    ("Room height", "X", "", "RoomGeometry.characteristic_height_m", "2.7 m"),
    ("North opaque wall area", "X", "", "OpaqueComponent.area_m2", "21.6 m2"),
    ("East opaque wall area", "X", "", "OpaqueComponent.area_m2", "16.2 m2"),
    ("South opaque wall area", "X", "", "OpaqueComponent.area_m2", "9.6 m2"),
    ("West opaque wall area", "X", "", "OpaqueComponent.area_m2", "16.2 m2"),
    ("Roof area", "X", "", "OpaqueComponent.area_m2", "48.0 m2"),
    ("Floor construction area", "X", "", "OpaqueComponent.area_m2", "48.0 m2"),
    ("South window area", "X", "", "TransparentComponent.area_m2", "12.0 m2"),
    ("Surface azimuths / tilts", "X", "", "OpaqueComponent/TransparentComponent azimuth_deg, tilt_from_horizontal_deg", "N/E/S/W=0/90/180/270 deg; walls 90 deg; roof 0 deg; floor 180 deg"),
    ("Wall U-value", "X", "", "OpaqueComponent.u_value_w_m2k", "0.53 W/(m2 K)"),
    ("Roof U-value", "X", "", "OpaqueComponent.u_value_w_m2k", "0.33 W/(m2 K)"),
    ("Floor U-value", "X", "", "OpaqueComponent.u_value_w_m2k", "0.038 W/(m2 K)"),
    ("Window U-value", "X", "", "TransparentComponent.baseline_u_value_w_m2k", "3.10 W/(m2 K)"),
    ("Window solar transmittance / g-value", "X", "", "TransparentComponent.solar_transmittance", "0.769"),
    ("Frame fraction and shading", "X", "", "TransparentComponent.frame_fraction, shading_factor", "0.0; 1.0"),
    ("Opaque solar absorptance", "X", "", "OpaqueComponent.absorptance", "0.60"),
    ("Surface long-wave emissivity", "X", "X", "OpaqueComponent/TransparentComponent.emissivity", "0.90"),
    ("Wall material layers (outside to room)", "X", "X", "OpaqueComponent.layers_room_to_outside (reversed by adapter)", "9 mm wood siding; 66 mm fiberglass; 12 mm plasterboard"),
    ("Roof material layers (outside to room)", "X", "X", "OpaqueComponent.layers_room_to_outside (reversed by adapter)", "19 mm roof deck; 111.8 mm fiberglass; 10 mm plasterboard"),
    ("Floor material layers", "X", "X", "OpaqueComponent.layers_room_to_outside", "1.003 m massless insulation; 25 mm timber"),
    ("Lightweight capacitance constraint", "X", "X", "construction-capacity reconciliation diagnostic", "42167 J/(m2 K); effective mass area factor 2.95"),
    ("Infiltration", "X", "", "VDI6007HourlyInput.ventilation_resistance_k_w", "0.414 1/h = 0.014904 m3/s; rho=1.20 kg/m3; cp=1005 J/(kg K); R=0.05561 K/W"),
    ("Mechanical / natural ventilation", "X", "", "hourly airflow adapter", "0.0 m3/s"),
    ("Internal sensible gain", "X", "", "VDI6007HourlyInput internal gains", "200 W, constant"),
    ("Internal gain split", "X", "X", "internal_convective_gain_w; internal_radiant_gain_w", "0.40 / 0.60 = 80 / 120 W"),
    ("Heating setpoint", "X", "", "run_thermostat_case heating_setpoint_schedule", "20.0 deg C, always available"),
    ("Cooling setpoint", "X", "", "run_thermostat_case cooling_setpoint_schedule", "27.0 deg C, always available"),
    ("HVAC load convention", "", "X", "OperationMode and total_hvac_load_w", "ideal unlimited load; heating positive, cooling negative"),
    ("Heating convective / radiant fractions", "", "X", "PreparedVDI6007Model.heating_installation (HVACFractions)", "0.60 / 0.40 (provisional VDI closure)"),
    ("Cooling convective / radiant fractions", "", "X", "PreparedVDI6007Model.cooling_installation (HVACFractions)", "0.30 / 0.70 (provisional VDI closure)"),
    ("VDI AW classification", "", "X", "OpaqueComponent.loading; TransparentComponent.loading", "all exterior walls, roof, floor and glazing = AW"),
    ("VDI IW proxy area", "", "X", "RoomGeometry.total_internal_surface_area_m2; IW OpaqueComponent", "96.0 m2 (2 x floor area; floor-plus-ceiling proxy, provisional)"),
    ("Inside total heat-transfer coefficient", "", "X", "prepare_model_case.inside_total_coefficient_w_m2k", "8.0 W/(m2 K), provisional"),
    ("Outside total heat-transfer coefficient", "X", "X", "OpaqueComponent.outside_alpha_total_w_m2k", "25.0 W/(m2 K), derived from Rse=0.04 m2 K/W"),
    ("VDI reference temperature", "", "X", "PreparedVDI6007Model.reference_temperature_c", "20.0 deg C, numerical reference"),
    ("Initial VDI storage state", "", "X", "zero_storage_state", "zero history at 20.0 deg C; no tuned warm-up"),
    ("Solar transposition", "", "X", "transpose_isotropic_sky_irradiance", "isotropic sky; ground reflectance 0.20; EPW DNI/DHI/GHI"),
    ("Long-wave sky boundary", "", "X", "ExteriorRadiationBoundary / exterior_boundary", "EPW horizontal infrared radiation; reference emissivity 0.93"),
]

HEADER = ["Input name", "Explicitly mentioned in BESTEST", "Required by VDI 6007", "RClib.vdi6007 implementation parameter", "Numerical value / choice"]

with (HERE / "case600_vdi_input_crosswalk.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(HEADER)
    writer.writerows(ROWS)

pilot_h, pilot_c = 4.657997, 5.802666
vdi_h, vdi_c = 3.4393486995589893, 4.479598886813768
vdi_ms_h, vdi_ms_c = 3.617693503127965, 3.700026013334109
area = 48.0

table_md = "\n".join(
    ["| " + " | ".join(HEADER) + " |", "|" + "|".join(["---"] * len(HEADER)) + "|"]
    + ["| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |" for row in ROWS]
)

report = f"""# Case 600 VDI 6007 input/output validation preview

## Decision

Use documented closure assumptions, but do not use location-based guesses to tune the answer. Preserve every BESTEST-prescribed quantity, take material layers from the repository's Modelica BESTEST Case 600 implementation, and guess only parameters that VDI 6007 mathematically requires but BESTEST does not prescribe. Those guesses remain provisional sensitivity parameters.

This is an equivalence-oriented cross-model comparison, not proof that VDI 6007 must reproduce a detailed Modelica solver exactly. The acceptance test remains the ASHRAE annual-energy range.

## Input crosswalk

An `X` in the BESTEST column means the parameter is stated by the canonical Case 600 record or its repository BESTEST implementation. An `X` in the VDI column means VDI needs the quantity explicitly even if another solver can leave it implicit. Some rows therefore contain two `X` marks.

{table_md}

## Annual output and EUI

| Run | Heating (MWh) | Heating EUI (kWh/m2 yr) | Cooling (MWh) | Cooling EUI (kWh/m2 yr) |
|---|---:|---:|---:|---:|
| VDI 6007 closure model | {vdi_h:.3f} | {vdi_h*1000/area:.3f} | {vdi_c:.3f} | {vdi_c*1000/area:.3f} |
| VDI 6007 + Modelica aggregate solar | {vdi_ms_h:.3f} | {vdi_ms_h*1000/area:.3f} | {vdi_ms_c:.3f} | {vdi_ms_c*1000/area:.3f} |
| Pilot notebook Modelica native | {pilot_h:.3f} | {pilot_h*1000/area:.3f} | {pilot_c:.3f} | {pilot_c*1000/area:.3f} |

VDI differs from the pilot Modelica result by {(vdi_h/pilot_h-1)*100:.1f}% for heating and {(vdi_c/pilot_c-1)*100:.1f}% for cooling. It is below the ASHRAE Case 600 limits in both cases: heating 3.75–4.98 MWh (78.125–103.750 kWh/m2 yr) and cooling 5.00–6.83 MWh (104.167–142.292 kWh/m2 yr).

The controlled-forcing VDI run reads the exact `solar_gain_W` column used by the pilot ISO + Modelica-solar run. It zeros VDI opaque short-wave irradiance and transmitted-window source channels, then adds the signed aggregate Modelica series to `internal_radiant_gain_w`. VDI long-wave exterior exchange is retained because the CSV is the pilot's aggregate zone-solar source, not a replacement weather boundary. The result is diagnostic only: the scalar CSV cannot preserve Modelica's surface-by-surface incidence or receiving-surface allocation.

## Input/output control

The notebook resolves paths from its own location, uses the checked-in JSON/CSV inputs, reads the same Denver TMY3 EPW family as the pilot, runs exactly 8760 hourly steps, and calculates energy from `total_hvac_load_w` as W x 1 h. Heating is the positive part and cooling is the magnitude of the negative part. EUI divides annual kWh by 48 m2. The pilot comparator is read from `results/case600/case600_metrics.csv`, the file produced by the pilot notebook's runner.

The simulation also asserts 8760 finite loads and reports the engine's maximum heat-balance residual. The reproduced residual is approximately 9.1e-13 W.

## Important limitations

- The VDI-required AW/IW topology, IW proxy, inside film coefficient, HVAC convective fractions, isotropic-sky transposition, ground reflectance, and initialization are not BESTEST calibration targets. They need sensitivity tests before interpreting disagreement.
- The floor's zero-capacity insulation is represented with tiny positive density and heat capacity (`1e-9`) because `MaterialLayer` requires positive values; this preserves the intended effectively massless layer.
- The repository VDI adapter requires an IW group even though Case 600 has no partition specification. Its inferred 96 m2 floor-plus-ceiling proxy is the largest unresolved equivalence issue.
- No numerical parameter was fitted to the pilot EUI. The current failure is evidence that the closure assumptions and/or VDI model-form treatment are not yet equivalent, not a reason to force the result into range.
- The controlled forcing gives {vdi_ms_h:.3f} MWh heating and {vdi_ms_c:.3f} MWh cooling. Cooling moves farther from Modelica, showing that native VDI solar replacement alone does not resolve the model-form/topology discrepancy.
"""
(HERE / "case600_vdi_validation_report.md").write_text(report, encoding="utf-8")

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.strip().splitlines()]}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [line + "\n" for line in text.strip().splitlines()]}

cells = [
    md("""# Case 600 — VDI 6007 closure model and EUI comparison

This notebook makes the VDI-specific closure assumptions visible and compares annual EUI with `01_case600_pilot_validation.ipynb`. It does not tune VDI parameters to match the pilot."""),
    code("""from pathlib import Path
from dataclasses import replace
import sys
import numpy as np
import pandas as pd

cwd = Path.cwd().resolve()
preview = next((p for p in (cwd, *cwd.parents) if (p / 'case600_defaults.json').is_file()), None)
if preview is None:
    candidate = cwd / '2_validation/_BESTEST/1_notebook/preview'
    if not (candidate / 'case600_defaults.json').is_file():
        raise FileNotFoundError('Open from preview or _development.')
    preview = candidate
development = next(p for p in (preview, *preview.parents) if (p / 'RC_br/RClib/vdi6007').is_dir())
bestest = development / '2_validation/_BESTEST'
sys.path.insert(0, str(development / 'RC_br'))

from RClib.vdi6007 import RCCase, run_thermostat_case

AREA_M2 = 48.0
WEATHER = development / '2_validation/modelica_test_2/modelica-buildings-github-master/Buildings/Resources/weatherdata/USA_CO_Denver.Intl.AP.725650_TMY3.epw'
assert WEATHER.is_file(), WEATHER"""),
    md("## Parameter crosswalk"),
    code("""crosswalk = pd.read_csv(preview / 'case600_vdi_input_crosswalk.csv').fillna('')
display(crosswalk)
print('BESTEST-explicit rows:', (crosswalk['Explicitly mentioned in BESTEST'] == 'X').sum())
print('VDI-required rows:', (crosswalk['Required by VDI 6007'] == 'X').sum())"""),
    md("## Run the annual VDI model\n\nInputs and outputs are controlled explicitly: fixed 8760-hour index, constant gains, fixed dual setpoints, no mechanical ventilation, and sign-separated ideal loads."),
    code("""case = RCCase(
    year=2023,
    loc_json=preview / 'case600_location.json',
    geo_json=preview / 'case600_geometry.json',
    default_json=preview / 'case600_defaults.json',
    epw_path=WEATHER,
    occupancy_profile_csv=preview / 'case600_occupancy.csv',
    use_construction_properties=True,
)
index = pd.date_range('2023-01-01 00:00', periods=8760, freq='h')
ones = np.ones(8760)
zeros = np.zeros(8760)
simulation = run_thermostat_case(
    case,
    index=index,
    gains_w=200.0,
    occupancy_fraction=ones,
    heating_setpoint_schedule=ones * 20.0,
    cooling_setpoint_schedule=ones * 27.0,
    heating_availability_schedule=ones.astype(bool),
    cooling_availability_schedule=ones.astype(bool),
    ventilation_fraction_schedule=zeros,
    heat_recovery_efficiency_schedule=zeros,
)
net_w = np.array([hour.total_hvac_load_w for hour in simulation.hourly_results])
assert len(net_w) == 8760 and np.isfinite(net_w).all()
vdi_heating_mwh = np.clip(net_w, 0, None).sum() / 1e6
vdi_cooling_mwh = np.clip(-net_w, 0, None).sum() / 1e6
print(f'VDI heating: {vdi_heating_mwh:.6f} MWh')
print(f'VDI cooling: {vdi_cooling_mwh:.6f} MWh')
print(f'Maximum absolute balance residual: {simulation.maximum_absolute_balance_residual_w:.3e} W')"""),
    md("""## Controlled forcing: VDI + the pilot's Modelica solar CSV

This mirrors the pilot ISO experiment at the available aggregate boundary. VDI native short-wave and transmitted-window sources are disabled; the CSV's signed zone-level source is injected as radiant heat. Exterior long-wave exchange remains active. This is diagnostic, not a formal ASHRAE result."""),
    code("""modelica_solar_csv = bestest / 'results/case600/case600_iso13790_diagnostic_modelica_solar_hourly.csv'
modelica_solar = pd.read_csv(modelica_solar_csv)
assert len(modelica_solar) == 8760
assert np.array_equal(modelica_solar['timestamp_s'].to_numpy(), np.arange(1, 8761) * 3600.0)
modelica_solar_w = modelica_solar['solar_gain_W'].to_numpy(float)

def use_modelica_aggregate_solar(position, hourly):
    no_opaque_shortwave = tuple(
        replace(boundary, direct_surface_irradiance_w_m2=0.0, diffuse_surface_irradiance_w_m2=0.0)
        for boundary in hourly.boundary_inputs
    )
    return replace(
        hourly,
        boundary_inputs=no_opaque_shortwave,
        exterior_radiant_sources=(),
        internal_radiant_gain_w=hourly.internal_radiant_gain_w + float(modelica_solar_w[position]),
    )

controlled_simulation = run_thermostat_case(
    case, index=index, gains_w=200.0, occupancy_fraction=ones,
    heating_setpoint_schedule=ones * 20.0, cooling_setpoint_schedule=ones * 27.0,
    heating_availability_schedule=ones.astype(bool), cooling_availability_schedule=ones.astype(bool),
    ventilation_fraction_schedule=zeros, heat_recovery_efficiency_schedule=zeros,
    hourly_input_transform=use_modelica_aggregate_solar,
)
controlled_net_w = np.array([hour.total_hvac_load_w for hour in controlled_simulation.hourly_results])
assert len(controlled_net_w) == 8760 and np.isfinite(controlled_net_w).all()
vdi_modelica_solar_heating_mwh = np.clip(controlled_net_w, 0, None).sum() / 1e6
vdi_modelica_solar_cooling_mwh = np.clip(-controlled_net_w, 0, None).sum() / 1e6
print(f'Modelica aggregate solar integral: {modelica_solar_w.sum()/1e6:.6f} MWh')
print(f'VDI + Modelica solar heating: {vdi_modelica_solar_heating_mwh:.6f} MWh')
print(f'VDI + Modelica solar cooling: {vdi_modelica_solar_cooling_mwh:.6f} MWh')
print(f'Maximum absolute balance residual: {controlled_simulation.maximum_absolute_balance_residual_w:.3e} W')"""),
    md("## Compare annual energy and EUI with the pilot notebook"),
    code("""metrics = pd.read_csv(bestest / 'results/case600/case600_metrics.csv')
def pilot_value(implementation, run_mode, metric):
    row = metrics[(metrics.implementation == implementation) & (metrics.run_mode == run_mode) & (metrics.metric == metric)]
    assert len(row) == 1, (implementation, run_mode, metric)
    return float(row.value.iloc[0])

runs = [
    ('VDI 6007 closure model', vdi_heating_mwh, vdi_cooling_mwh),
    ('VDI 6007 + Modelica aggregate solar', vdi_modelica_solar_heating_mwh, vdi_modelica_solar_cooling_mwh),
    ('Pilot: Modelica native', pilot_value('modelica', 'native', 'annual_heating_energy'), pilot_value('modelica', 'native', 'annual_cooling_energy')),
    ('Pilot: ISO + Modelica solar', pilot_value('iso13790', 'diagnostic_modelica_solar', 'annual_heating_energy'), pilot_value('iso13790', 'diagnostic_modelica_solar', 'annual_cooling_energy')),
    ('Pilot: ISO native', pilot_value('iso13790', 'native', 'annual_heating_energy'), pilot_value('iso13790', 'native', 'annual_cooling_energy')),
]
comparison = pd.DataFrame(runs, columns=['Run', 'Heating (MWh)', 'Cooling (MWh)'])
comparison['Heating EUI (kWh/m2 yr)'] = comparison['Heating (MWh)'] * 1000 / AREA_M2
comparison['Cooling EUI (kWh/m2 yr)'] = comparison['Cooling (MWh)'] * 1000 / AREA_M2
base = comparison.loc[comparison.Run == 'Pilot: Modelica native'].iloc[0]
comparison['Heating vs Modelica (%)'] = (comparison['Heating (MWh)'] / base['Heating (MWh)'] - 1) * 100
comparison['Cooling vs Modelica (%)'] = (comparison['Cooling (MWh)'] / base['Cooling (MWh)'] - 1) * 100
display(comparison.round(3))"""),
    code("""bounds = {'Heating': (3.75, 4.98), 'Cooling': (5.00, 6.83)}
status = pd.DataFrame({
    'Metric': ['Heating', 'Cooling'],
    'VDI (MWh)': [vdi_heating_mwh, vdi_cooling_mwh],
    'ASHRAE lower (MWh)': [bounds['Heating'][0], bounds['Cooling'][0]],
    'ASHRAE upper (MWh)': [bounds['Heating'][1], bounds['Cooling'][1]],
})
status['Status'] = np.where(
    status['VDI (MWh)'].between(status['ASHRAE lower (MWh)'], status['ASHRAE upper (MWh)']),
    'PASS', 'FAIL'
)
display(status.round(3))
print('Conclusion: the untuned VDI closure model is stable, but it is not yet equivalent to the pilot within the ASHRAE annual ranges.')"""),
    md("""## Interpretation

The input mapping is reproducible, but the result is not yet equivalent: both annual loads are low. Do not tune arbitrary location-based guesses to erase this gap. Prioritize sensitivity/verification of the VDI-only IW proxy, HVAC radiative split, inside film coefficient, floor boundary representation, and solar/long-wave preprocessing. The detailed parameter rationale and limitations are in `case600_vdi_validation_report.md`."""),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
(HERE / "case600_vdi_validation.ipynb").write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print("Built report, crosswalk, and notebook in", HERE)
