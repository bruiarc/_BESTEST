"""Build the two readable, executable Case 600 VDI audit notebooks."""
from pathlib import Path
import nbformat as nbf

HERE = Path(__file__).resolve().parent

def md(s): return nbf.v4.new_markdown_cell(s)
def code(s): return nbf.v4.new_code_cell(s)

common = """from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path.cwd().resolve()
if HERE.name != '2_vdi':
    HERE = HERE / '2_validation/_BESTEST/2_vdi'
sys.path.insert(0, str(HERE))
import bestest_vdi_case600_analysis as analysis
pd.set_option('display.max_columns', 30)
plt.style.use('seaborn-v0_8-whitegrid')"""

validation_cells = [
 md("""# Case 600 — VDI controlled and native-solar validation

This preview compares the 96 m² IW closure with the no-IW wrapper at 0.414 ACH. Heating HVAC, cooling HVAC, and the 200 W internal sensible gain are all 100% convective. The primary pair uses identical Modelica aggregate solar; native VDI solar is a secondary pair. No 0.5 ACH simulation is included and no parameter is selected to force a pass.

**Acceptance ranges:** heating 3.75–4.98 MWh/year and cooling 5.00–6.83 MWh/year. All EUI values use 48.0 m²."""),
 code(common),
 md("""## Recompute the controlled and native pairs

`run_four_cases()` builds each annual case from the checked-in Case 600 inputs. For controlled forcing it sets every native VDI opaque short-wave channel to zero, removes transmitted-window radiant sources, and adds `solar_gain_W` once to `internal_radiant_gain_w`. Exterior long-wave processing is untouched."""),
 code("controlled, native, hourly = analysis.run_four_cases()\nvdi_cases = controlled[controlled.case.isin(list('AB'))]\nassert len(vdi_cases) == 2\nassert not np.isclose(vdi_cases['infiltration_ACH'], 0.5).any()\nassert vdi_cases['annual_solar_MWh'].nunique() == 1\nassert (vdi_cases[['heating_convective_fraction','cooling_convective_fraction','internal_gain_convective_fraction']] == 1.0).all().all()\nassert (vdi_cases['solar_source'] == 'Modelica aggregate controlled forcing').all()\ndisplay(controlled.round(3))"),
 md("## Main controlled-solar validation result"),
 code("cols=['case','topology','infiltration_ACH','HVAC_split','heating_convective_fraction','cooling_convective_fraction','internal_gain_convective_fraction','heating_MWh','cooling_MWh','total_HVAC_MWh','heating_EUI_kWh_m2yr','cooling_EUI_kWh_m2yr','total_EUI_kWh_m2yr','peak_heating_kW','peak_cooling_kW','heating_hours','cooling_hours','annual_solar_MWh','heating_pass','cooling_pass','combined_pass']\ndisplay(controlled[cols].round(3))"),
 md("""## Secondary native-VDI-solar result

These runs answer a forcing sensitivity question only. They are not used to prefer either topology."""),
 code("display(native[cols].round(3))"),
 md("## Annual energy and EUI comparison"),
 code("fig, axes=plt.subplots(1,2,figsize=(12,4.2)); plot=controlled.set_index('case'); plot[['heating_MWh','cooling_MWh']].plot.bar(ax=axes[0],color=['#d95f02','#1b9e77']); axes[0].axhspan(3.75,4.98,color='#d95f02',alpha=.08); axes[0].axhspan(5.00,6.83,color='#1b9e77',alpha=.08); axes[0].set_ylabel('Annual energy (MWh)'); plot[['heating_EUI_kWh_m2yr','cooling_EUI_kWh_m2yr']].plot.bar(ax=axes[1],color=['#d95f02','#1b9e77']); axes[1].set_ylabel('EUI (kWh/m² yr)'); plt.tight_layout(); plt.show()"),
 md("## Selected-period HVAC profiles"),
 code("feb=hourly[(pd.to_datetime(hourly.timestamp)>=pd.Timestamp('2023-02-01')) & (pd.to_datetime(hourly.timestamp)<pd.Timestamp('2023-02-04'))]; fig,ax=plt.subplots(figsize=(12,4));\nfor case,g in feb.groupby('case'): ax.plot(pd.to_datetime(g.timestamp),g.HVAC_load_W/1000,label=case,linewidth=1.2)\nax.axhline(0,color='black',linewidth=.7); ax.set_ylabel('HVAC load (kW; heating +)'); ax.legend(ncol=4); fig.autofmt_xdate(); plt.show()"),
 md("""## Interpretation

The controlled pair isolates topology at 0.414 ACH while holding solar and all three convective allocations fixed. The native-solar pair is secondary. Modelica remains a reference, not a fitting target.

Outputs are saved in `results/case600_vdi_four_case/`."""),
]

sensitivity_cells = [
 md("""# Case 600 — remaining VDI parameter sensitivity

This notebook audits no-IW at 0.414 ACH with controlled Modelica solar and a 100% convective baseline for heating HVAC, cooling HVAC, and internal sensible gain. No 0.5 ACH simulation is included."""),
 code(common),
 md("## Baseline and source trace\n\nThe RClib HVAC fractions enter `derive_hvac_fractions`, then `allocate_hvac_load`; convective load is injected in the air balance and radiant load at AW/IW receiving nodes. Because the fixed-temperature equation contains these fractions, they affect thermostat load determination as well as post-solution distribution. Modelica Case 600 instead connects its single `PrescribedHeatFlow` directly to `zonHVAC.heaPorAir`, controlled from `TAir`: its ideal HVAC is purely convective."),
 code("split, surface, allocation, initialization, summary = analysis.run_sensitivities()\nbase=analysis.metrics('baseline',analysis.simulate(),'Modelica aggregate controlled forcing',analysis.solar_series().sum()/1e6)\npd.Series(base).to_frame('value')"),
 md("## HVAC convective/radiant split"),
 code("display(split[['sensitivity','convective_fraction','radiant_fraction','heating_EUI_kWh_m2yr','cooling_EUI_kWh_m2yr','peak_heating_kW','peak_cooling_kW','heating_hours','cooling_hours','zero_fraction_treatment']].round(3)); fig,axes=plt.subplots(1,2,figsize=(11,4));\nfor name,g in split.groupby('sensitivity'): axes[0].plot(g.convective_fraction,g.heating_EUI_kWh_m2yr,'o-',label=name); axes[1].plot(g.convective_fraction,g.cooling_EUI_kWh_m2yr,'o-',label=name)\naxes[0].set_ylabel('Heating EUI (kWh/m² yr)'); axes[1].set_ylabel('Cooling EUI (kWh/m² yr)'); [a.set_xlabel('Convective fraction') for a in axes]; axes[0].legend(); axes[1].legend(); plt.tight_layout(); plt.show()"),
 md("""Exact zero was attempted first. The allocation arithmetic produces `-1.11e-16` and the fraction validator rejects it; the 0% rows therefore use `1e-9` and are explicitly labelled numerical diagnostics. This is an implementation endpoint defect, not evidence that VDI mathematically requires a nonzero fraction."""),
 md("## Inside heat-transfer coefficient"),
 code("display(surface.round(3))"),
 md("## Radiative allocation and topology"),
 code("display(allocation.round(4))"),
 md("""The controlled scalar source is injected into `internal_radiant_gain_w`. The standard topology distributes it by receiving area between AW and the 96 m² IW branch; no-IW sends 100% to AW. Thus removing IW changes both storage topology and the solar/internal-radiant receiving weights. This is not equivalent to Modelica's `phiSur`/`phiMas` receiving-surface calculation and is a high-priority closure issue."""),
 md("## Initialization / warm-up"),
 code("display(initialization.round(5)); delta=initialization.set_index('initialization').diff().iloc[-1]; display(delta.to_frame('warm minus cold'))"),
 md("## Envelope, floor, long-wave, gains, and airflow audit"),
 code("display(pd.read_csv(analysis.OUTS/'case600_vdi_floor_boundary_audit.csv')); print(f\"0.414 ACH flow = {0.414*129.6/3600:.5f} m³/s; RClib ventilation conductance = {1.20*1005*0.414*129.6/3600:.3f} W/K\")"),
 md("""Layer-only resistance and film check:

| Assembly | Layer-only R (m²K/W) | Rsi used in target check | Rse | Total R | Derived U | Target U |
|---|---:|---:|---:|---:|---:|---:|
| Wall | 1.789 | 0.0577 | 0.040 | 1.887 | 0.530 | 0.530 |
| Roof | 2.997 | -0.0069* | 0.040 | 3.030 | 0.330 | 0.330 |
| Floor | 25.253 | 1.023 | 0.040 | 26.316 | 0.038 | 0.038 |

`*` The roof layer sum is already slightly more resistive than the prescribed total U-value, demonstrating that layers and prescribed U cannot simultaneously define films exactly. RClib uses prescribed U for whole-assembly boundary conductance but also passes Rse into the reduced-network residual. That mixed convention is unresolved and can double-count/misallocate film resistance in dynamics even though steady boundary weighting uses U.

The floor remains an AW with an outdoor-equivalent boundary in the VDI input, matching the local Modelica parameters `AFlo=48`, `UFlo=.038`, `b=1` at the aggregate ISO level. Its 1.003 m insulation proxy is effectively massless and timber stores heat. BESTEST's very low-U floor is not a license to make it adiabatic.

Internal sensible gain is prescribed as 200 W and is assigned 100% to air in this requested comparison. The local Modelica ISO model instead sends 50% to air (`phiAir(k=0.5)`) and distributes the remainder to surface/mass, so this is recorded as a closure assumption rather than claimed equivalence. Exterior long-wave remains explicit in VDI."""),
 md("## Suspicious-parameter ranking"),
 code("display(summary)"),
 md("""## Conclusion

The strongest demonstrated sensitivity is the HVAC delivery split, and the strongest topology-coupled concern is radiant redistribution when the 96 m² IW receiver disappears. Initialization is classified from the measured annual deltas, not intuition. Inside coefficient sensitivity is bounded by documented comparator/conventional values. Surface-film consistency, floor representation, and exterior long-wave remain evidence-led audits rather than tuned switches. See `case600_vdi_remaining_parameter_findings.md` and the CSVs in `results/case600_vdi_remaining_sensitivity/`."""),
]

for name,cells in [("bestest_vdi_case600_four_case_validation.ipynb",validation_cells),("case600_vdi_remaining_parameter_sensitivity.ipynb",sensitivity_cells)]:
    nb=nbf.v4.new_notebook(cells=cells, metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3"}})
    nbf.write(nb,HERE/name)
