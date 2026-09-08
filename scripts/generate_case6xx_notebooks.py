#!/usr/bin/env python3
"""Generate data-driven, presentation-equivalent 6XX report notebooks."""
from pathlib import Path
import json
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
CASES = ("610", "620", "630", "640", "650", "660", "670", "680", "685", "695")

SETUP = '''from pathlib import Path
import json, sys
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display
ISO_MODE = "modelica_solar"  # "modelica_solar" or "native"
root = Path.cwd()
if not (root / "scripts").is_dir(): root = root.parent
sys.path.insert(0, str(root / "scripts"))
from bestest_reporting import annual_energy_table, completed_hour_label, markdown_table, selected_iso_mode
from case6xx_reporting import annual_tracks, comparison_table, peak_tracks, prescribed_changes, range_judgement
case = CASE
out = root / "results" / f"case{case}"
reference = root / "_ref" / "BESTEST_LBNL_all_cases_reference.md"
metrics = pd.read_csv(out / f"case{case}_metrics.csv")
solar = pd.read_csv(out / f"case{case}_solar_comparison.csv")
references = pd.concat([pd.DataFrame([{"case": r.Case, "metric": metric, "lower": float(r.Lower), "upper": float(r.Upper)} for _, r in markdown_table(reference, section).iterrows()]) for section, metric in (("Annual heating energy reference data", "annual_heating_energy"), ("Annual cooling energy reference data", "annual_cooling_energy"))], ignore_index=True)
_, ISO_LABEL = selected_iso_mode(ISO_MODE)'''

def cell(kind, source):
    return nbf.v4.new_markdown_cell(source) if kind == "md" else nbf.v4.new_code_cell(source)

def annual_plot(metric):
    return f'''table=annual_energy_table(metrics, reference, case, "{metric}", ISO_MODE)
display(table)
row=table.iloc[0]; labels=["Modelica native", ISO_LABEL]; values=[row["Modelica native"],row[ISO_LABEL]]
fig,ax=plt.subplots(figsize=(7,3.4)); ax.bar(labels,values,color=["#4C78A8","#F58518"])
ax.axhline(row["ASHRAE lower"],color="#555",linestyle="--",label="ASHRAE lower"); ax.axhline(row["ASHRAE upper"],color="#555",linestyle="--",label="ASHRAE upper")
ax.set(title=f"Case {{case}}: {metric.replace('_',' ')}",ylabel="MWh",ylim=(0,max(values+[row["ASHRAE upper"]])*1.2)); ax.legend(fontsize=8); ax.grid(axis="y",alpha=.25); fig.tight_layout(); plt.show()'''

def peak_plot(column, title):
    return f'''peaks=peak_tracks(metrics, completed_hour_label)
fig,ax=plt.subplots(figsize=(7,3.4)); ax.bar(peaks["Track"],peaks["{column}"],color=["#4C78A8","#72B7B2","#F58518"])
ax.set(title=f"Case {{case}}: {title}",ylabel="kW",ylim=(0,peaks["{column}"].max()*1.2 if peaks["{column}"].max() else 1)); ax.grid(axis="y",alpha=.25); fig.tight_layout(); plt.show()'''

def build(case, index):
    changes = json.loads((ROOT / "inputs" / "case6xx_deltas.json").read_text())["cases"][case]["changes"]
    details = "\n".join(f"- {change}" for change in changes)
    cells = [
        cell("md", f"# Case {case} BESTEST validation\n\nNative ISO is the formal ASHRAE 140 result. `modelica_solar` is a controlled-forcing comparative run and is not a formal result."),
        cell("code", f'CASE="{case}"\n' + SETUP),
        cell("md", f"## 1. Case definition\n\nCase {case} inherits Case 600 with these explicit BESTEST changes:\n\n{details}\n\nWeather: Denver TMY3; non-leap calendar; simulation/output timestep: 1 h."),
        cell("code", "display(prescribed_changes(case)); base=json.loads((root/'inputs'/'case600.json').read_text()); display(pd.DataFrame([{\"Geometry\":f\"{base['geometry']['floor_area_m2']} m² floor; {base['geometry']['volume_m3']} m³ volume\",\"Construction\":base['constructions']['mass_class'],\"Weather\":base['weather']['identifier'],\"Timestep\":\"1 h\"}])); display(pd.read_csv(root/'inputs'/'case600_adapter_mapping.csv')[['quantity','ashrae_value','ashrae_unit','modelica_parameter','iso_parameter','mapping_type']])"),
        cell("md", "## 2. Annual heating and cooling\n\nThree computed tracks, MWh."), cell("code", "display(annual_tracks(metrics))"),
        cell("md", "## 3. Annual energy validation outcome\n\nFormal annual-energy judgement for native ISO only."), cell("code", "display(range_judgement(metrics,references,case))"),
        cell("md", "## 4. Annual heating figure\n\nAnnual heating energy with published ASHRAE limits."), cell("code", annual_plot("annual_heating_energy")),
        cell("md", "## 5. Annual cooling figure\n\nAnnual cooling energy with published ASHRAE limits."), cell("code", annual_plot("annual_cooling_energy")),
        cell("md", "## 6. Peak heating and cooling\n\nComputed peak loads and completed-hour occurrence times."), cell("code", "display(peak_tracks(metrics,completed_hour_label))"),
        cell("md", "## 7. Peak-load comparison figures\n\nComputed peak loads, kW."), cell("code", peak_plot("Peak heating kW","peak heating load")+"\n"+peak_plot("Peak cooling kW","peak cooling load")),
        cell("md", "## 8. Daily load profile\n\nThe LBNL presentation requires daily load profiles only for Cases 600 and 900; none is added for this 6XX case."),
        cell("md", "## 9. Solar forcing\n\nAnnual zone-solar totals, MWh."), cell("code", "solar_report=solar.set_index('quantity').T; solar_report['Absolute difference MWh']=(solar_report['native_rclib_zone_solar_MWh']-solar_report['modelica_resolved_zone_solar_MWh']).abs(); solar_report['Relative difference %']=(solar_report['native_modelica_ratio']-1)*100; display(solar_report.reset_index(drop=True))"),
        cell("md", "## 10. Controlled-forcing agreement\n\nISO + Modelica solar minus Modelica native; diagnostic only."), cell("code", 'display(comparison_table(metrics,"controlled_modelica"))'),
        cell("md", "## 11. Native versus controlled-forcing effect\n\nEffect of changing only solar forcing in ISO."), cell("code", 'display(comparison_table(metrics,"solar_effect").query("Metric in [\'Annual heating\', \'Annual cooling\']"))'),
        cell("md", "## 12. Final case outcome\n\nConcise formal-native and controlled-forcing record."), cell("code", "judgement=range_judgement(metrics,references,case); summary=annual_tracks(metrics).set_index('Run'); summary['Formal ASHRAE status']=['; '.join(judgement['Formal status']),'diagnostic','reference implementation']; display(summary.reset_index()); print('Native ISO formal annual status:','; '.join(judgement['Formal status'])); print('Controlled forcing remains a Modelica-comparative diagnostic; no new schema or timestamp mapping is introduced.')")]
    notebook=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.11"}})
    nbf.write(notebook,ROOT/"notebooks"/f"{index:02d}_case{case}_validation.ipynb")

def build_summary():
    cells = [
        cell("md", "# BESTEST Cases 600–695 summary\n\nAnnual, peak, solar, and native-ISO results for the conditioned 6XX family."),
        cell("code", "from pathlib import Path\nimport sys,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\nroot=Path.cwd(); root=root if (root/'results').is_dir() else root.parent\nsys.path.insert(0,str(root/'scripts'))\nfrom case6xx_reporting import annual_tracks,comparison_table\nCASES=('600','610','620','630','640','650','660','670','680','685','695')\nmetrics={case:pd.read_csv(root/'results'/f'case{case}'/f'case{case}_metrics.csv') for case in CASES}"),
        cell("md", "## Annual heating and cooling"),
        cell("code", "annual=pd.concat([annual_tracks(metrics[case]).assign(Case=case) for case in CASES]); display(annual.pivot(index='Case',columns='Run',values=['Heating MWh','Cooling MWh']))\nfor metric in ('Heating MWh','Cooling MWh'):\n    fig,ax=plt.subplots(figsize=(8,3.5)); annual.pivot(index='Case',columns='Run',values=metric).plot(kind='bar',ax=ax); ax.set_ylabel(metric); ax.grid(axis='y',alpha=.25); fig.tight_layout(); plt.show()"),
        cell("md", "## Controlled-forcing residuals and solar"),
        cell("code", "residual=pd.concat([comparison_table(metrics[case],'controlled_modelica').assign(Case=case) for case in CASES]); display(residual.pivot(index='Case',columns='Metric',values='Difference %'))\nsolar=[]\nfor case in CASES:\n    values=pd.read_csv(root/'results'/f'case{case}'/f'case{case}_solar_comparison.csv').set_index('quantity').value\n    solar.append({'Case':case,'Native solar MWh':values['native_rclib_zone_solar_MWh'],'Modelica solar MWh':values['modelica_resolved_zone_solar_MWh']})\ndisplay(pd.DataFrame(solar))")]
    notebook=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.11"}})
    nbf.write(notebook,ROOT/"notebooks"/"14_cases6xx_summary.ipynb")

if __name__ == "__main__":
    for index, case in enumerate(CASES,start=4): build(case,index)
    build_summary()
