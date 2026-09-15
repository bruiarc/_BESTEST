# VDI Case 900 and 6XX/9XX transfer-validation plan

## Objective

Test whether the Case-600-derived F36/F52 implementation pattern transfers to
Case 900 and the available paired 6XX/9XX cases. The configuration is a
candidate implementation, not a universal validated solution, and no case is
independently optimized to enter its accepted range.

## Carry-forward implementation

Both candidates use no-IW topology, layer-controlled dynamics, the existing
VDI total inside coefficient of 8 W/(m²K), harmonised exterior long-wave,
50% air/50% AW internal gains, native VDI solar, 100% convective ideal HVAC,
and benchmark geometry, schedules, setpoints, and airflow.

- F36-like: native VDI area allocation (100% of transmitted solar to AW under
  no-IW).
- F52-like: comparator-derived air fraction, with the non-air remainder
  projected to AW because no IW node exists.

## Case 900 translation

Geometry, U-values, glazing, infiltration, gains, weather, schedules, and
controls remain those of Case 600. Case 900 changes the mass class from
lightweight to heavyweight, with aggregate capacity 307750 J/(m²K) of floor
area and effective mass-area factor 2.43.

No authoritative heavyweight material layers exist locally. The approved
proxy preserves layer thickness, conductivity, density, surface assignment,
and prescribed U-values, while multiplying layer specific heats by
5.405964196971026 so the pre-reduction opaque capacity is exactly
14.772 MJ/K. This is comparator-derived and not fitted to model output. The
2.43 effective-area factor is recorded but not separately applied because the
no-IW VDI network has no direct equivalent.

Before simulation, each input is classified as unchanged, benchmark-prescribed
change, comparator-derived, implementation assumption, or unresolved
provenance. Simulation is prohibited until the mass and resistance audits pass.

## Case 900 experiment and gate

Run only F36-like and F52-like initially. Compare against heating
1.04–2.28 MWh and cooling 2.35–2.60 MWh. For each load, distance to a range is
`max(lower-value, 0, value-upper)` and the combined distance is normalized by
the corresponding range widths.

- Pass: both loads in range; carry that configuration forward.
- Slight failure: `0 < D_MWh_norm <= 0.25`; stop and audit only the mass
  translation before changing anything.
- Material failure: `D_MWh_norm > 0.25`; stop and diagnose mass-relevant
  topology/capacity placement without launching a factorial search.
- Integrity failure: not 8760 finite hours, source inconsistency, or maximum
  balance residual above 1e-9 W; stop regardless of range result.

The checked-in Case 900 cooling interval excludes the repository Modelica
result (2.284 MWh); retain it provisionally and report the inconsistency.

## Available sequence

Matched pairs are 600/900, 610/910 (south shading), 620/920 (east/west
windows), 630/930 (east/west windows plus shading), 640/940 (heating setback),
650/950 (day cooling plus night ventilation), 680/980 (low wall/roof U),
685/985 (narrow deadband), and 695/995 (low U plus narrow deadband). Cases 660
and 670 are lightweight-only glazing-property tests and are reported
separately.

For every variant, report absolute range status and within-family heating and
cooling deltas from its base. Compare each VDI delta with the sign, median, and
min/max envelope of deltas calculated independently for the published
reference programs. Also compare 9XX-minus-6XX mass effects for matched pairs.

Case 910 cooling remains unresolved until its malformed 2.00/0.86 bounds are
verified. Cases 650/950 require heating within 1e-9 MWh of zero; a failed
zero-width heating interval has undefined normalized distance.

## Reusable checklist

1. IW topology: Is the intended topology present, and are consequences of an
   absent IW explicit?
2. Solar/source allocation: Which nodes receive solar, and is the allocation
   native, comparator-derived, or projected?
3. Envelope convention: Which inputs control transmission and dynamics, and
   are U-values, films, layers, and capacities reconciled?
4. Inside heat transfer: Which total convention is active, and how is it split
   between convection and radiation?
5. Exterior long-wave: Is it native or harmonised, and what is replaced?
6. Internal gains: Which nodes receive sensible gains, and what is the source
   of the split?
7. Airflow: What quantity and provenance are used, and is conversion applied
   exactly once?
8. Geometry, schedules, controls: Do they match the case definition and retain
   consistent ideal-control semantics?

Each case records separate `current setting` and `source/provenance` fields.

## Planned artefacts

- `2_vdi/doc/bestest_vdi_transfer_engine.py`
- `2_vdi/inputs/case900_defaults.json`
- `2_vdi/case900_vdi_validation.ipynb`
- `2_vdi/bestest_6xx_9xx_validation.ipynb`
- `_ref/vdi_case900_6xx_9xx_validation_report.md`
- New result directories under `2_vdi/results/`

Existing Case 600 notebooks, CSVs, and `_issue.md` remain unchanged.
