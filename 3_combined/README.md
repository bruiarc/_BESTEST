# Combined BESTEST annual-load comparison

`build_annual_load_comparison.py` renders the requested combined 5R1C/7R2C
comparison from cached results only. It never executes Modelica, RClib, or VDI
models.

The generated `outputs/annual_load_comparison.csv` contains 40 rows: annual
heating and cooling for the 20 conditioned BESTEST cases. Its selected outcomes
are mapped as follows:

| Column | Cached source |
|---|---|
| `LBNL-5R1C` | Published LBNL `Modelica ISO13790` value in `reference/BESTEST_LBNL_EUI.md` |
| `5R1C` | `RClib-ISO + Modelica-resolved solar`: `iso13790` + `diagnostic_modelica_solar` in `results/1_iso/case*/case*_metrics.csv` |
| `7R2C` | `F36` / `F36-like` row in `results/2_vdi/bestest_6xx_9xx_ashrae140_layers/annual_results.csv` |

Use [BESTEST_LBNL_EUI_5R1C_7R2C.ipynb](BESTEST_LBNL_EUI_5R1C_7R2C.ipynb) for
the interactive workflow. It builds the cache, displays the 40-row comparison,
and shows both figures without rerunning models.

The equivalent command-line operation, from the repository root, is:

```bash
python 3_combined/build_annual_load_comparison.py
```

It creates a reference-style table figure and a second grouped-column figure.
Orange values are outside valid benchmark bounds. Case 910 cooling retains the
source table's reversed limits and is intentionally not given a pass/fail
colour.
