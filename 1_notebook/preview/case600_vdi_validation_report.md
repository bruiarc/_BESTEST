    # Case 600 VDI 6007 input/output validation preview

    ## Decision

    Use documented closure assumptions, but do not use location-based guesses to tune the answer. Preserve every BESTEST-prescribed quantity, take material layers from the repository's Modelica BESTEST Case 600 implementation, and guess only parameters that VDI 6007 mathematically requires but BESTEST does not prescribe. Those guesses remain provisional sensitivity parameters.

    This is an equivalence-oriented cross-model comparison, not proof that VDI 6007 must reproduce a detailed Modelica solver exactly. The acceptance test remains the ASHRAE annual-energy range.

    ## Input crosswalk

    An `X` in the BESTEST column means the parameter is stated by the canonical Case 600 record or its repository BESTEST implementation. An `X` in the VDI column means VDI needs the quantity explicitly even if another solver can leave it implicit. Some rows therefore contain two `X` marks.

    | Input name | Explicitly mentioned in BESTEST | Required by VDI 6007 | RClib.vdi6007 implementation parameter | Numerical value / choice |
    |---|---|---|---|---|
    | Location / weather station | X |  | RCCase.epw_path; solar weather_location | Denver TMY3 / 39.83 deg N, -104.65 deg E |
    | Simulation year and calendar | X |  | RCCase.year; hourly index | 2023 surrogate non-leap year; 8760 h |
    | Timestep | X |  | RCCase.timestep_hours | 1 h |
    | Floor area | X |  | RoomGeometry.floor_area_m2 | 48.0 m2 |
    | Room volume | X |  | RoomGeometry.volume_m3 | 129.6 m3 |
    | Room height | X |  | RoomGeometry.characteristic_height_m | 2.7 m |
    | North opaque wall area | X |  | OpaqueComponent.area_m2 | 21.6 m2 |
    | East opaque wall area | X |  | OpaqueComponent.area_m2 | 16.2 m2 |
    | South opaque wall area | X |  | OpaqueComponent.area_m2 | 9.6 m2 |
    | West opaque wall area | X |  | OpaqueComponent.area_m2 | 16.2 m2 |
    | Roof area | X |  | OpaqueComponent.area_m2 | 48.0 m2 |
    | Floor construction area | X |  | OpaqueComponent.area_m2 | 48.0 m2 |
    | South window area | X |  | TransparentComponent.area_m2 | 12.0 m2 |
    | Surface azimuths / tilts | X |  | OpaqueComponent/TransparentComponent azimuth_deg, tilt_from_horizontal_deg | N/E/S/W=0/90/180/270 deg; walls 90 deg; roof 0 deg; floor 180 deg |
    | Wall U-value | X |  | OpaqueComponent.u_value_w_m2k | 0.53 W/(m2 K) |
    | Roof U-value | X |  | OpaqueComponent.u_value_w_m2k | 0.33 W/(m2 K) |
    | Floor U-value | X |  | OpaqueComponent.u_value_w_m2k | 0.038 W/(m2 K) |
    | Window U-value | X |  | TransparentComponent.baseline_u_value_w_m2k | 3.10 W/(m2 K) |
    | Window solar transmittance / g-value | X |  | TransparentComponent.solar_transmittance | 0.769 |
    | Frame fraction and shading | X |  | TransparentComponent.frame_fraction, shading_factor | 0.0; 1.0 |
    | Opaque solar absorptance | X |  | OpaqueComponent.absorptance | 0.60 |
    | Surface long-wave emissivity | X | X | OpaqueComponent/TransparentComponent.emissivity | 0.90 |
    | Wall material layers (outside to room) | X | X | OpaqueComponent.layers_room_to_outside (reversed by adapter) | 9 mm wood siding; 66 mm fiberglass; 12 mm plasterboard |
    | Roof material layers (outside to room) | X | X | OpaqueComponent.layers_room_to_outside (reversed by adapter) | 19 mm roof deck; 111.8 mm fiberglass; 10 mm plasterboard |
    | Floor material layers | X | X | OpaqueComponent.layers_room_to_outside | 1.003 m massless insulation; 25 mm timber |
    | Lightweight capacitance constraint | X | X | construction-capacity reconciliation diagnostic | 42167 J/(m2 K); effective mass area factor 2.95 |
    | Infiltration | X |  | VDI6007HourlyInput.ventilation_resistance_k_w | 0.414 1/h = 0.014904 m3/s; rho=1.20 kg/m3; cp=1005 J/(kg K); R=0.05561 K/W |
    | Mechanical / natural ventilation | X |  | hourly airflow adapter | 0.0 m3/s |
    | Internal sensible gain | X |  | VDI6007HourlyInput internal gains | 200 W, constant |
    | Internal gain split | X | X | internal_convective_gain_w; internal_radiant_gain_w | 0.40 / 0.60 = 80 / 120 W |
    | Heating setpoint | X |  | run_thermostat_case heating_setpoint_schedule | 20.0 deg C, always available |
    | Cooling setpoint | X |  | run_thermostat_case cooling_setpoint_schedule | 27.0 deg C, always available |
    | HVAC load convention |  | X | OperationMode and total_hvac_load_w | ideal unlimited load; heating positive, cooling negative |
    | Heating convective / radiant fractions |  | X | PreparedVDI6007Model.heating_installation (HVACFractions) | 0.60 / 0.40 (provisional VDI closure) |
    | Cooling convective / radiant fractions |  | X | PreparedVDI6007Model.cooling_installation (HVACFractions) | 0.30 / 0.70 (provisional VDI closure) |
    | VDI AW classification |  | X | OpaqueComponent.loading; TransparentComponent.loading | all exterior walls, roof, floor and glazing = AW |
    | VDI IW proxy area |  | X | RoomGeometry.total_internal_surface_area_m2; IW OpaqueComponent | 96.0 m2 (2 x floor area; floor-plus-ceiling proxy, provisional) |
    | Inside total heat-transfer coefficient |  | X | prepare_model_case.inside_total_coefficient_w_m2k | 8.0 W/(m2 K), provisional |
    | Outside total heat-transfer coefficient | X | X | OpaqueComponent.outside_alpha_total_w_m2k | 25.0 W/(m2 K), derived from Rse=0.04 m2 K/W |
    | VDI reference temperature |  | X | PreparedVDI6007Model.reference_temperature_c | 20.0 deg C, numerical reference |
    | Initial VDI storage state |  | X | zero_storage_state | zero history at 20.0 deg C; no tuned warm-up |
    | Solar transposition |  | X | transpose_isotropic_sky_irradiance | isotropic sky; ground reflectance 0.20; EPW DNI/DHI/GHI |
    | Long-wave sky boundary |  | X | ExteriorRadiationBoundary / exterior_boundary | EPW horizontal infrared radiation; reference emissivity 0.93 |

    ## Annual output and EUI

    | Run | Heating (MWh) | Heating EUI (kWh/m2 yr) | Cooling (MWh) | Cooling EUI (kWh/m2 yr) |
    |---|---:|---:|---:|---:|
    | VDI 6007 closure model | 3.439 | 71.653 | 4.480 | 93.325 |
    | VDI 6007 + Modelica aggregate solar | 3.618 | 75.369 | 3.700 | 77.084 |
    | Pilot notebook Modelica native | 4.658 | 97.042 | 5.803 | 120.889 |

    VDI differs from the pilot Modelica result by -26.2% for heating and -22.8% for cooling. It is below the ASHRAE Case 600 limits in both cases: heating 3.75–4.98 MWh (78.125–103.750 kWh/m2 yr) and cooling 5.00–6.83 MWh (104.167–142.292 kWh/m2 yr).

    The controlled-forcing VDI run reads the exact `solar_gain_W` column used by the pilot ISO + Modelica-solar run. It zeros VDI opaque short-wave irradiance and transmitted-window source channels, then adds the signed aggregate Modelica series to `internal_radiant_gain_w`. VDI long-wave exterior exchange is retained because the CSV is the pilot's aggregate zone-solar source, not a replacement weather boundary. The result is diagnostic only: the scalar CSV cannot preserve Modelica's surface-by-surface incidence or receiving-surface allocation.

    ## Input/output control

    The notebook resolves paths from its own location, uses the checked-in JSON/CSV inputs, reads the same Denver TMY3 EPW family as the pilot, runs exactly 8760 hourly steps, and calculates energy from `total_hvac_load_w` as W x 1 h. Heating is the positive part and cooling is the magnitude of the negative part. EUI divides annual kWh by 48 m2. The pilot comparator is read from `results/case600/case600_metrics.csv`, the file produced by the pilot notebook's runner.

    The simulation also asserts 8760 finite loads and reports the engine's maximum heat-balance residual. The reproduced residual is approximately 9.1e-13 W.

    ## Important limitations

    - The VDI-required AW/IW topology, IW proxy, inside film coefficient, HVAC convective fractions, isotropic-sky transposition, ground reflectance, and initialization are not BESTEST calibration targets. They need sensitivity tests before interpreting disagreement.
    - The floor's zero-capacity insulation is represented with tiny positive density and heat capacity (`1e-9`) because `MaterialLayer` requires positive values; this preserves the intended effectively massless layer.
    - The repository VDI adapter requires an IW group even though Case 600 has no partition specification. Its inferred 96 m2 floor-plus-ceiling proxy is the largest unresolved equivalence issue.
    - No numerical parameter was fitted to the pilot EUI. The current failure is evidence that the closure assumptions and/or VDI model-form treatment are not yet equivalent, not a reason to force the result into range.
    - The controlled forcing gives 3.618 MWh heating and 3.700 MWh cooling. Cooling moves farther from Modelica, showing that native VDI solar replacement alone does not resolve the model-form/topology discrepancy.
