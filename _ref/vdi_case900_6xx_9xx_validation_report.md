# VDI Case 900 and 6XX/9XX transfer-validation report

## 1. Objective

Test whether the Case-600-derived F36/F52 implementation pattern transfers to
Case 900 without case-specific optimization, then use the predeclared gate to
decide whether wider 6XX/9XX validation may proceed.

## 2. Carry-forward implementation from Case 600

Both candidates retain no-IW topology, layer-controlled dynamics, total inside
coefficient 8 W/(m²K), harmonised exterior long-wave, 50% air/50% AW internal
gains, native VDI solar, 100% convective ideal HVAC, and benchmark geometry,
weather, schedules, setpoints, and airflow.

- F36-like uses native VDI area allocation.
- F52-like uses the comparator-derived air fraction and projects the non-air
  remainder to AW.

The generalized runner reproduced the stored Case 600 F36 and F52 annual
heating and cooling values with zero difference at stored precision before the
Case 900 runs were accepted.

## 3. Case-by-case benchmark input differences

Case 900 retains all Case 600 prescribed inputs except thermal mass:

- capacity density changes from 42,167 to 307,750 J/(m²K);
- aggregate capacity changes from 2.024016 to 14.772 MJ/K;
- effective mass-area factor changes from 2.95 to 2.43.

Because authoritative heavyweight layers are absent locally, the test uses the
approved capacity-constrained proxy. Case 600 layer thicknesses,
conductivities, densities, surface assignment, and prescribed U-values are
retained; specific heats are multiplied by 5.405964196971026. The audited
pre-reduction layer capacity is 14.772 MJ/K. The effective-area factor is
recorded but not separately applied because there is no direct no-IW VDI
mapping.

## 4. Eight-point implementation checklist

| Category | Current Case 900 setting | Status |
|---|---|---|
| IW topology | no-IW | carried forward |
| Solar/source allocation | F36-like and F52-like | controlled pair |
| Envelope convention | explicit layers with capacity proxy; prescribed U retained | assumption declared |
| Inside heat transfer | total 8 W/(m²K) | carried forward |
| Exterior long-wave | harmonised to outdoor dry bulb | carried forward |
| Internal-gain allocation | 50% air, 50% AW | carried forward |
| Airflow | 0.414 h⁻¹, applied once | comparator-consistent; canonical provenance open |
| Geometry/schedules/controls | Case 900 benchmark record; 20/27 °C ideal control | checked |

The full reusable questions, settings, and provenance are stored in
`case900_eight_point_checklist.csv`.

## 5. Annual heating/cooling results

| Configuration | Heating (MWh) | Cooling (MWh) | Maximum balance residual (W) |
|---|---:|---:|---:|
| F36-like | 2.521021 | 2.783916 | 4.55e-13 |
| F52-like | 2.509007 | 2.839874 | 4.55e-13 |

Both simulations contain 8,760 finite hourly records. Numerical integrity is
not a credible explanation for the discrepancy.

## 6. BESTEST range checks

The checked-in ranges are 1.04–2.28 MWh heating and 2.35–2.60 MWh cooling.

| Configuration | Heating status | Cooling status | Both | Normalized distance |
|---|---|---|---|---:|
| F36-like | above upper bound | above upper bound | fail | 0.760908 |
| F52-like | above upper bound | above upper bound | fail | 0.977110 |

Both exceed the predeclared material-failure threshold of 0.25. The Case 900
cooling range itself remains provenance-sensitive because it excludes the
repository Modelica result of 2.284 MWh; it was not altered here.

## 7. Paired 6XX/9XX response-pattern checks

Not executed. The approved Case 900 gate prohibits wider simulations when
both carry-forward candidates fail materially. The planned pairs and response
metrics remain recorded in the planning document and gated notebook.

## 8. Remaining discrepancies and provenance issues

- The capacity-constrained proxy matches total mass but may place heavyweight
  storage incorrectly across the VDI AW states.
- The ISO effective mass area of 116.64 m² has no direct no-IW VDI mapping.
- Layer-derived dynamics and prescribed U-value boundary conductance remain a
  mixed convention.
- Infiltration is repository-consistent at 0.414 h⁻¹, but canonical benchmark
  provenance remains open.
- Native opaque and transmitted solar contributions are not equivalent to the
  comparator's unified signed solar object.
- Case 910 cooling bounds remain malformed and were not used.

## 9. Final implementation decision

**STOP.** Neither F36-like nor F52-like transfers successfully to Case 900
under the approved heavyweight proxy, so no configuration is carried into the
wider 6XX/9XX sequence. The next task must isolate heavyweight capacity
placement and effective-area semantics in the no-IW VDI network. It must not
optimize unrelated factors or repeat a broad factorial search.

## Diagnostic history

Detailed input classifications, layer calculations, hourly traces, and
machine-readable results remain under `2_vdi/results/case900_vdi_transfer/`.
They are supporting evidence and are kept separate from the final decision.
