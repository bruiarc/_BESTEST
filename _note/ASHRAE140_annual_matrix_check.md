# ASHRAE 140 annual-load matrix check

The generated matrix follows the LBNL annual heating/cooling table presentation and adds two data-derived columns: `Modelica actual` and `RClib.iso13790.solar`. Orange/red cells indicate values outside a valid published lower/upper interval. Case 910 cooling is deliberately not coloured because the bundled reference has reversed limits (2.00 lower, 0.86 upper).

## Modelica reconciliation

The 40 annual values integrated from the centralized Modelica standardized hourly outputs reproduce the `Modelica ISO13790` values published in the LBNL table to within **0.000597 MWh**. This is consistent with the published table being rounded to three decimals.

The same three cooling cells are outside valid acceptance intervals in both the published LBNL Modelica column and the actual Modelica results:

| Case | Metric | Modelica MWh | Published interval MWh |
|---|---|---:|---:|
| 670 | Cooling | 4.975 | 5.05–7.67 |
| 900 | Cooling | 2.284 | 2.35–2.60 |
| 985 | Cooling | 5.905 | 5.95–7.26 |

Thus, yes: the reference LBNL Modelica ISO 13790 presentation itself has three red annual-energy cells. This is a documented reporting fact, not a Python-specific issue.

## Native ISO count

For formal validation, native ISO has **27 red cells** across the 39 metrics with valid numeric bounds: 11 heating and 16 cooling. It remains available in the machine-readable audit and formal tables, but is deliberately omitted from this comparative figure. The displayed RClib-ISO column uses Modelica-resolved solar and is diagnostic only.

## Generated artifacts

- `results/ashrae140_annual_load_matrix.png`
- `results/ashrae140_annual_load_matrix.csv`
- `scripts/plot_ashrae140_annual_matrix.py`
