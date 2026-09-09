# 9XX BESTEST execution report

## Scope and execution contract

Cases 910, 920, 930, 940, 950, 980, 985 and 995 were run through the existing Buildings Modelica runner and the shared Python ISO 13790 pipeline. Modelica raw and standardized outputs are retained only under `_modelica/results/CaseXXX/`; `_BESTEST/results/caseXXX/` retains the two ISO tracks and derived result tables.

Each notebook defaults to `ISO_MODE = "modelica_solar"`, while retaining `"native"` as a switchable Python mode. Native ISO alone is the formal ASHRAE 140 candidate. Controlled forcing is comparative only.

## Completed results

All rows below are MWh. `H/C status` is native ISO heating/cooling against the parsed ASHRAE range. Controlled residuals are ISO + Modelica solar minus Modelica native.

| Case | Modelica | Native ISO | Controlled ISO | H/C status | Controlled H/C residual % | Native / Modelica solar MWh | Notebook |
|---|---|---|---|---|---|---|---|
| 910 | 2.284 / 1.675 | 5.049 / 0.499 | 2.269 / 1.675 | FAIL / FAIL | -0.62 / 0.02 | 3.654 / 10.247 | executed |
| 920 | 3.650 / 2.684 | 3.540 / 2.110 | 3.635 / 2.689 | PASS / FAIL | -0.41 / 0.16 | 8.626 / 9.350 | executed |
| 930 | 4.183 / 1.920 | 4.101 / 1.498 | 4.169 / 1.923 | PASS / PASS | -0.34 / 0.16 | 6.771 / 7.340 | executed |
| 940 | 1.242 / 2.251 | 3.794 / 0.613 | 1.151 / 2.247 | FAIL / FAIL | -7.34 / -0.17 | 4.270 / 12.112 | executed |
| 950 | 0.000 / 0.638 | 0.000 / 0.102 | 0.000 / 0.655 | PASS / FAIL | 0.00 / 2.58 | 4.270 / 12.112 | executed; zero heating is prescribed |
| 980 | 0.494 / 3.658 | 2.601 / 0.834 | 0.487 / 3.665 | FAIL / FAIL | -1.46 / 0.21 | 3.972 / 11.563 | executed |
| 985 | 2.333 / 5.905 | 4.828 / 2.522 | 2.310 / 5.898 | FAIL / FAIL | -1.00 / -0.13 | 4.270 / 12.112 | executed |
| 995 | 0.927 / 7.077 | 2.685 / 2.509 | 0.913 / 7.080 | FAIL / FAIL | -1.59 / 0.03 | 3.972 / 11.563 | executed |

## Notebook completion check

Every individual notebook contains: explicit Case-900 delta and common-input/mapping tables; three-track annual table; native formal range table; annual heating/cooling figures; three-track peak table and two peak figures; solar table; controlled-forcing residual table; native-to-controlled effect table; and final summary. Each has 25 cells, at least 17 captured outputs and four embedded figures. The family summary is also executed.

## QA

- Modelica: all eight annual cases succeeded; standardised hourly files contain 8,760 rows.
- ISO native and controlled forcing: all eight cases succeeded; each track contains 8,760 rows and finite annual/peak/solar metrics.
- Notebook execution: all eight reports and `02_cases9xx_summary.ipynb` executed with the working `eplus_env` Jupyter kernel. The default `python3` kernel remains unsuitable because it dies before replying to `kernel_info`.
- Automated tests: `13 passed` (`pytest -q`), including the parameterised 9XX artifact, schema, output, figure, and native/diagnostic separation test.

## Remaining issue

Native ISO solar totals remain lower than Modelica-resolved totals in several cases; the completed controlled-forcing tables make this visible without using controlled forcing for formal ASHRAE status. This is the pre-existing solar-preprocessing issue, not a new 9XX mapping or timestamp failure.
