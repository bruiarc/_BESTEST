#!/usr/bin/env python3
"""Generate the 9XX reports with the Case 900 presentation contract."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bestest_iso_generate_case6xx_notebooks as template
import nbformat as nbf

CASES = ("910", "920", "930", "940", "950", "980", "985", "995")
NAMES = ("02a", "02b", "02c", "02d", "02e", "02f", "02g", "02h")

def main():
    template.DELTA_FILE = "case9xx_deltas.json"
    template.BASE_INPUT = "case900.json"
    template.MAPPING_INPUT = "case900_adapter_mapping.csv"
    template.REPORT_MODULE = "bestest_iso_case9xx_reporting"
    for case, name in zip(CASES, NAMES):
        template.build(case, 0)
        old = template.ROOT / "notebooks" / f"00_case{case}_validation.ipynb"
        old.rename(template.ROOT / "notebooks" / f"{name}_case{case}_validation.ipynb")
    cells = [nbf.v4.new_markdown_cell("# BESTEST Cases 900–995 summary\n\nAnnual, peak, solar, and native-ISO results for the conditioned 9XX family."),
             nbf.v4.new_code_cell("from pathlib import Path\nimport sys,pandas as pd,matplotlib.pyplot as plt\nfrom IPython.display import display\ncwd=Path.cwd().resolve()\nroot=next((p for p in (cwd,*cwd.parents) if (p/'scripts/bestest_iso_reporting.py').is_file()),None)\nif root is None: raise FileNotFoundError('Could not locate the BESTEST repository root')\nsys.path.insert(0,str(root/'scripts'))\nfrom bestest_iso_reporting import completed_hour_label\nfrom bestest_iso_case9xx_reporting import annual_tracks,comparison_table,peak_tracks\nCASES=('900','910','920','930','940','950','980','985','995')\nmetrics={case:pd.read_csv(root/'results'/'1_iso'/f'case{case}'/f'case{case}_metrics.csv') for case in CASES}"),
             nbf.v4.new_markdown_cell("## Annual heating and cooling"),
             nbf.v4.new_code_cell("annual=pd.concat([annual_tracks(metrics[case]).assign(Case=case) for case in CASES]); display(annual.pivot(index='Case',columns='Run',values=['Heating MWh','Cooling MWh']))\nfor metric in ('Heating MWh','Cooling MWh'):\n    fig,ax=plt.subplots(figsize=(8,3.5)); annual.pivot(index='Case',columns='Run',values=metric).plot(kind='bar',ax=ax); ax.set_ylabel(metric); ax.grid(axis='y',alpha=.25); fig.tight_layout(); plt.show()"),
             nbf.v4.new_markdown_cell("## Controlled-forcing residuals, peaks, and solar"),
             nbf.v4.new_code_cell("residual=pd.concat([comparison_table(metrics[case],'controlled_modelica').assign(Case=case) for case in CASES]); display(residual.pivot(index='Case',columns='Metric',values='Difference %'))\npeaks=pd.concat([peak_tracks(metrics[case],completed_hour_label).assign(Case=case) for case in CASES]); display(peaks)\nsolar=[]\nfor case in CASES:\n    values=pd.read_csv(root/'results'/f'case{case}'/f'case{case}_solar_comparison.csv').set_index('quantity').value\n    solar.append({'Case':case,'Native solar MWh':values['native_rclib_zone_solar_MWh'],'Modelica solar MWh':values['modelica_resolved_zone_solar_MWh']})\ndisplay(pd.DataFrame(solar))")]
    nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec":{"display_name":"Python (eplus_env)","language":"python","name":"eplus_env"},"language_info":{"name":"python"}})
    nbf.write(nb, template.ROOT / "notebooks" / "02_cases9xx_summary.ipynb")

if __name__ == "__main__": main()
