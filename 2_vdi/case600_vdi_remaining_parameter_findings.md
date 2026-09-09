# Case 600 VDI remaining-parameter findings

## Scope and baseline

The principal baseline is the structural no-IW wrapper, 0.414 ACH, 200 W sensible gain, 20/27 °C air-temperature setpoints, and the identical 12.112389 MWh/year Modelica aggregate solar series. Heating HVAC, cooling HVAC, and internal sensible gain are all 100% convective. Native VDI short-wave inputs are zeroed and the aggregate solar source is added once to `internal_radiant_gain_w`; exterior long-wave exchange remains active. The baseline recomputes to 5.572790 MWh heating and 4.720118 MWh cooling. No 0.5 ACH simulation or optimizer is used.

## Material findings

- HVAC delivery split materially affects both annual loads. From the new 100% convective baseline, moving heating toward the radiant endpoint raises heating from 5.573 to 8.300 MWh. Moving cooling toward its radiant endpoint raises cooling from 4.720 to 7.175 MWh. This is a cross-model closure assumption, not a BESTEST tuning parameter.
- The local Buildings/IBPSA Case 600 ideal HVAC is purely convective. `Case600.mo` connects `preHeaCoo.port` to `zonHVAC.heaPorAir`; the heating and cooling PID controllers sense `zonHVAC.TAir`. It does not prescribe radiant HVAC to a surface or operative-temperature control.
- Exact zero HVAC convection is not mathematically singular in the no-IW equations, but the current area-weighted allocation creates a `-1.11e-16` floating residual and rejects it as outside [0,1]. Only the explicitly labelled endpoint diagnostics use `1e-9`. This endpoint behavior is a likely implementation issue.
- Solar/radiant redistribution changes fundamentally with topology. In the 96 m² IW case, radiant source allocation is area-weighted between AW and IW; in no-IW, 100% is delivered to AW. Consequently the topology experiment changes receiving area, storage, and radiant coupling together. This is a high-priority likely implementation/closure issue and plausibly explains why both heating and cooling rise.
- The inside coefficient is a combined value in RClib: a fixed 5 W/(m² K) radiant coefficient is subtracted to derive room-side convection. Across 7.7, 8.0, and 9.1 W/(m² K), heating changes 0.275 MWh and cooling changes 1.006 MWh under the new baseline.
- Initialization is low impact annually. One repeated-year warm-up changes annual heating by +0.00471 MWh and cooling by -0.000006 MWh.
- At 0.414 ACH and 129.6 m³, flow is 0.014904 m³/s. With density 1.20 kg/m³ and specific heat 1005 J/(kg K), ventilation conductance is 17.974 W/K. There is one ACH-to-flow conversion and no extra schedule multiplier.

## Modelica HVAC source trace

| File | Component/model | Heat connector | Interpretation | Relevance to VDI closure |
|---|---|---|---|---|
| `Buildings/.../BESTEST/Cases6xx/Case600.mo` | `preHeaCoo` | `zonHVAC.heaPorAir` | Pure convective heat flow to air | Supports 100% convective sensitivity as comparator evidence, not a fitted choice |
| `Buildings/.../ISO13790/Zone5R1C/Zone.mo` | `heaAir` | air heat port/network | Air-node sensible heat | Confirms connector path |
| `IBPSA/.../BESTEST/Cases6xx/Case600.mo` | `preHeaCoo` | `zonHVAC.heaPorAir` | Same pure-convective path | Independent local library copy agrees |
| `RClib/vdi6007/sources.py` and solver paths | `allocate_hvac_load` | air plus star/AW/IW terms | Mixed according to provisional fractions | Fractions affect thermostat load equation and distribution |

## Envelope, floor, gains, and long-wave audit

The material-layer resistances are 1.789 m²K/W (wall), 2.993 m²K/W (roof), and 25.254 m²K/W (floor). Against prescribed U-values, adding Rse=0.04 leaves implied inside resistances of about 0.058, -0.003, and 1.022 m²K/W respectively. The roof inconsistency proves the layer set, prescribed U, and conventional films cannot all be exact simultaneously. RClib uses prescribed U for whole-assembly boundary conductance while also passing exterior film resistance into reduced-network residual construction. This mixed steady/dynamic convention remains **UNRESOLVED** and should be corrected by specification mapping, never by EUI fit.

The current floor uses a 1.003 m effectively massless insulation proxy plus 25 mm timber, is classified AW, and receives the outdoor-equivalent boundary. The local Modelica ISO Case 600 has `AFlo=48`, `UFlo=0.038`, and `b=1`; it is not simply adiabatic. The candidate VDI representation remains AW with careful boundary/resistance reconciliation.

BESTEST prescribes 200 W sensible internal gain. This requested comparison maps it 100% convectively. The local Modelica Zone5R1C instead has `phiAir(k=0.5)` and divides the remainder between surface and mass, so the new setting is recorded as an explicit closure assumption rather than claimed equivalence.

The VDI path explicitly uses EPW horizontal infrared radiation with surface emissivity 0.90 and reference emissivity 0.93. The local ISO13790 comparator has no equivalent explicit exterior-surface long-wave network, so a like-for-like annual surface flux cannot be extracted from its aggregate model. The difference is a model-form issue and remains unresolved; long-wave was not disabled.

## Classification

- Materially affects heating: HVAC heat split; likely topology-coupled radiant redistribution.
- Materially affects cooling: HVAC cooling split; inside combined coefficient; radiant redistribution.
- Affects both: HVAC split and the removal/reallocation of the IW radiant receiver.
- Likely implementation problems: exact-zero fraction rejection; possible surface-film/residual inconsistency; topology-coupled area allocation that prevents an isolated capacitance comparison.
- Legitimate VDI closure assumptions: HVAC delivery fractions, inside combined coefficient, explicit long-wave boundary, and AW/IW receiving topology.
- Prescribed and not tunable: 0.414 ACH, 129.6 m³, 48 m², envelope U-values, 200 W sensible gain, 20/27 °C setpoints, and the controlled solar series for the main comparison.
- Low-impact assumption: 20 °C zero-history initialization for annual energy.

The no-IW topology should **not** be rejected based on heating alone. Its closer structural relationship to a one-element network is still credible, but current radiant redistribution and mixed closure assumptions prevent interpreting its annual energy as a topology-only test.
