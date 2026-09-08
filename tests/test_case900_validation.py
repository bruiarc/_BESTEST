from pathlib import Path
import json
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'modelica_test_2'))

def test_case900_inputs_and_outputs():
    data=json.loads((ROOT/'inputs/case900.json').read_text())
    assert data['case']=='900' and data['constructions']['mass_class']=='heavyweight'
    assert data['constructions']['mass_capacity_J_m2K']==307750.0
    subprocess.run([sys.executable,'scripts/run_case900_validation.py'],cwd=ROOT,check=True)
    out=ROOT/'results/case900'; metrics=pd.read_csv(out/'case900_metrics.csv')
    assert len(pd.read_csv(out/'case900_iso13790_native_hourly.csv'))==8760
    assert set(metrics.run_mode)=={'native','diagnostic_modelica_solar'}
    assert metrics.loc[(metrics.implementation=='modelica')&(metrics.run_mode=='native'),'value'].notna().all()
    formal=pd.read_csv(out/'case900_formal_ashrae_energy.csv')
    assert set(formal.metric)=={'annual_heating_energy','annual_cooling_energy'}
    assert not formal.loc[formal.implementation.eq('iso13790'),'within_ashrae_range'].any()
    profile=pd.read_csv(out/'case900_feb1_load_profile.csv')
    assert len(profile)==72 and profile.timestamp_s.min()==2682000
    assert 'Case900' in __import__('iso_validation.bestest_pipeline',fromlist=['CASE_DEFINITIONS']).CASE_DEFINITIONS['900'].modelica_class
