# Case 900 validation report

**READY FOR BATCH GENERALISATION.** Case 900 uses
`Buildings.ThermalZones.ISO13790.Validation.BESTEST.Cases9xx.Case900` through
the same cached-Modelica extraction, standard schema, native ISO run, and
controlled-forcing ISO run as Case 600. No new mapping, schema, or timestamp
issue was found.

| Track | Heating (MWh) | Cooling (MWh) |
|---|---:|---:|
| Modelica native | 1.832767 | 2.284410 |
| ISO native | 4.790196 | 0.614339 |
| ISO + Modelica-resolved solar | 1.818536 | 2.284475 |

Native ISO fails the published annual ranges: heating 1.04–2.28 MWh and
cooling 2.35–2.60 MWh. The Modelica native cooling value (2.284410 MWh) is
also below the published lower limit; this is retained as a source discrepancy,
not reinterpreted.

Peaks (Modelica / controlled ISO): heating 2.639677 / 2.646536 kW at 3,391,200
s; cooling 2.365476 / 2.373074 kW at 23,641,200 s. Controlled-forcing residuals
are -0.014232 MWh heating, +0.000065 MWh cooling, +0.006859 kW peak heating,
and +0.007599 kW peak cooling.

Native RClib zone solar is 4.270377 MWh; Modelica-resolved solar is 12.112389
MWh (difference 7.842012 MWh, 64.74% of Modelica). This repeats the established
solar-preprocessing separation; it does not require Case 900-specific logic.
