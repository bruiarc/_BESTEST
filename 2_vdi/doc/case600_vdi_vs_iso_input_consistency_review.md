# Why the VDI Case 600 result differs from BESTEST while ISO is close

## Executive summary

The evidence points primarily to **model-input translation inconsistency**, rather than a numerical solver problem.

The close ISO result is a controlled-forcing diagnostic: the Python ISO 13790 5R1C model is given the Modelica-resolved hourly solar gain. It produces 4.582 MWh heating and 5.728 MWh cooling, close to the Modelica result of 4.658 and 5.803 MWh. This is expected because the two models share a similar 5R1C abstraction and, in this diagnostic, the most influential and difficult-to-reproduce input—hourly solar—is identical.

The VDI model also receives the same annual Modelica solar series, but several other inputs do not represent the same physical model. In particular, the standard VDI adapter invents 96 m² of internal-wall area; the no-IW alternative removes both its storage and its radiant receiving area; surface coefficients and material reductions are assumed; exterior long-wave exchange is added explicitly; and prescribed assembly U-values are mixed with layer-derived dynamic properties and film resistances. The VDI cases are therefore not controlled translations of BESTEST 600.

There is no sign that initialization or an algebraic energy-balance error explains the discrepancy: annual warm-up sensitivity is negligible and the reported balance residual is approximately `9e-13 W`.

## Numerical comparison

| Run | Heating (MWh) | Cooling (MWh) | Interpretation |
|---|---:|---:|---|
| BESTEST accepted range | 3.75–4.98 | 5.00–6.83 | Published comparison range used by the repository |
| Modelica ISO13790 comparator | 4.658 | 5.803 | Passes both ranges |
| Python ISO + Modelica solar | 4.582 | 5.728 | Close to Modelica; diagnostic controlled forcing |
| Python ISO native solar | 5.502 | 1.414 | Not close; shows that native solar preprocessing is itself unresolved |
| VDI, inferred 96 m² IW + Modelica solar | 3.172 | 2.980 | Both too low |
| VDI, no IW + Modelica solar | 5.573 | 4.720 | Heating too high; cooling slightly below range |

Consequently, it is too broad to say that “ISO is close” without qualification. **ISO is close only after its native solar calculation is replaced by Modelica-resolved solar.** That experiment proves that the ISO thermal network behaves similarly under matched forcing; it does not validate all native ISO inputs.

## Input-consistency findings

### 1. The VDI internal-wall input is invented and has a first-order effect

BESTEST 600 does not prescribe a 96 m² internal-wall element. The VDI adapter creates it as `2 × floor area`. This is recorded in the audit as an implementation fallback, not a benchmark input.

Its effect is very large: with otherwise controlled settings, introducing this IW changes heating from 5.573 to 3.172 MWh and cooling from 4.720 to 2.980 MWh. The result crosses from excessive heating in the no-IW model to insufficient heating in the IW model. This is the strongest direct evidence that the VDI mismatch is driven by topology/input construction.

The comparison is also not an isolated capacitance test. Removing IW simultaneously:

- removes the IW resistance and capacitance;
- reduces total radiant receiving area from AW + 96 m² to AW only;
- redirects 100% of the controlled radiant solar source to AW;
- changes the distribution of any radiant internal or HVAC source.

Thus neither topology is yet demonstrably the correct VDI representation of BESTEST 600.

### 2. Equal total solar does not mean equal solar input to the thermal network

For the controlled VDI run, native opaque and window short-wave paths are disabled and the Modelica aggregate solar series is inserted once as `internal_radiant_gain_w`. This correctly avoids simple double counting and matches the annual 12.112 MWh solar total.

However, Modelica ISO distributes non-air gains through its surface/mass formulation, whereas VDI allocates the injected radiant source by AW/IW receiving area. The hourly scalar is equal, but the **node, receiving area, storage path, and time response are not**. This explains why matching annual solar alone does not reproduce ISO loads, particularly cooling.

The native VDI solar total is 12.803 MWh, about 5.7% above the controlled Modelica series. Native no-IW cooling rises from 4.720 to 5.284 MWh, confirming that solar processing matters, but it does not explain the much larger IW-topology discrepancy.

### 3. Envelope steady-state and dynamic inputs are assembled from inconsistent conventions

The VDI input supplies both prescribed whole-assembly U-values and explicit material layers. RClib uses the U-values for boundary conductance while using layer properties and an exterior film resistance in the reduced dynamic network.

The layer resistance, prescribed U-value, and conventional films cannot all be simultaneously satisfied. The roof is the clearest example: its layers give approximately 2.997 m²K/W, already greater than `1/U = 3.030 m²K/W` after allowing for only the stated exterior film, leaving a negative implied inside resistance. The floor uses a 1.003 m, effectively massless insulation proxy plus timber to force the very low U-value.

This mixed mapping can alter both steady loss and dynamic storage. ISO's aggregate 5R1C model uses the prescribed U-values more directly, so it has fewer opportunities for this inconsistency.

### 4. Surface heat-transfer coefficients are not matched

The VDI closure uses an inside total coefficient of 8.0 W/(m²·K), then subtracts a fixed 5 W/(m²·K) radiative coefficient to obtain convection. The Modelica ISO comparator uses `hSur = 9.1 W/(m²·K)` in its aggregate network.

This is materially important, especially for cooling. Raising the VDI value from 8.0 to 9.1 changes the no-IW result from 5.573/4.720 to 5.778/5.452 MWh. Cooling enters the accepted range, although heating moves farther above it. This is evidence of unmatched input meaning, not justification to tune the coefficient to the target.

### 5. Exterior long-wave boundary treatment is not like-for-like

VDI explicitly processes EPW horizontal infrared radiation using surface emissivity 0.90 and reference emissivity 0.93. The ISO 5R1C comparator has no equivalent explicit exterior-surface long-wave network. Even with identical dry-bulb weather and short-wave solar, the effective exterior surface boundary is therefore different.

This is a legitimate model-form closure choice, but until isolated it prevents attributing the residual difference to VDI physics alone.

### 6. Gain and HVAC splits are closure assumptions, not BESTEST inputs

The reviewed VDI run assigns the 200 W sensible internal gain and ideal heating/cooling loads as 100% convective. Modelica's HVAC connector is indeed purely convective, but its internal gain is not: the local ISO model sends 50% to air and distributes the remainder to surface and mass.

The HVAC split is highly influential in VDI because it enters thermostat load determination, not merely post-processing. Moving heating from fully convective to fully radiant raises annual heating from 5.573 to 8.300 MWh; doing the same for cooling raises cooling from 4.720 to 7.175 MWh. The selected 100% convective HVAC setting is the best-supported comparator choice, but the inconsistent internal-gain split remains.

### 7. Airflow is internally consistent in the reviewed runs, but benchmark provenance needs resolution

Both the ISO comparator and current VDI study use 0.414 ACH. In VDI this is converted once using 129.6 m³ to 0.014904 m³/s and approximately 17.97 W/K. No duplicate conversion or schedule multiplier was found.

Nevertheless, the older input audit records an unresolved expectation of 0.5 ACH for canonical BESTEST 600. If the objective is strict ASHRAE 140 reproduction rather than consistency with this repository's Modelica case, the source of 0.414 ACH must be documented or corrected in **all** comparators. It should not be changed only in VDI.

### 8. Floor semantics remain ambiguous

The VDI model classifies the floor as an exterior AW subject to its outdoor-equivalent boundary. The local Modelica aggregate representation uses `AFlo=48`, `UFlo=0.038`, and `b=1`. These may match in nominal conductance but are not necessarily dynamically or radiatively equivalent, especially with VDI's explicit long-wave/solar boundary and synthetic material layers.

### 9. Initialization is not a credible explanation

Repeating a warm-up year changes annual heating by only about 0.0047 MWh and cooling by about 0.000006 MWh. This is negligible compared with the topology and boundary-condition effects.

## Likely explanation, ranked

1. **Unprescribed IW topology and topology-coupled radiant redistribution** — demonstrated multi-MWh effect and the clearest model-input inconsistency.
2. **Non-equivalent placement of the matched aggregate solar gain** — identical watts, different receiving nodes and storage response.
3. **Mixed U-value/layer/film construction mapping** — internally irreconcilable for at least the roof and potentially changes both conductance and dynamics.
4. **Unmatched inside surface coefficient and explicit VDI exterior long-wave treatment** — demonstrated material cooling sensitivity and different boundary physics.
5. **Internal-gain allocation mismatch** — VDI uses 100% air while ISO splits the prescribed 200 W between air and thermal mass/surfaces.
6. **Floor boundary and layer semantics** — nominal U-value is shared, but the dynamic and radiative mapping is not proven equivalent.
7. **Air-change provenance** — consistent between current runs, but possibly inconsistent with canonical BESTEST 600.
8. **Initialization/numerics** — evidence indicates negligible impact; not a likely cause.

## Conclusion

The ISO controlled-forcing result is close because it is effectively a matched-input, closely related network comparison: weather timing, aggregate solar, prescribed conductances, setpoints, and a 5R1C-style thermal abstraction are aligned. Its poor native-solar cooling result also demonstrates that closeness disappears when a major input pipeline is not aligned.

The VDI calculation is farther away because the conversion from BESTEST inputs into VDI-required parameters is underdetermined and currently includes consequential assumptions. Most importantly, its IW area, source allocation, material reduction, films, surface coefficients, and long-wave boundary do not describe the same effective model as ISO/Modelica. The present results therefore measure a combination of **VDI model-form difference and inconsistent input closure**, not a clean failure of VDI 6007 against BESTEST.

Before judging VDI accuracy, a controlled crosswalk should hold the physical boundary conductances, capacitance allocation, source-node fractions, surface coefficients, floor boundary, long-wave convention, airflow, and hourly solar treatment equivalent wherever the two model forms permit. Any remaining discrepancy after that exercise would be a defensible model-form difference.
