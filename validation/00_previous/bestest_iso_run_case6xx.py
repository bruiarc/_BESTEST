#!/usr/bin/env python3
"""Parameterised 6XX BESTEST runner; shared by every 6XX report notebook."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; LEGACY=ROOT.parent/'modelica_test_2'; MODEL=ROOT.parent/'_modelica/results'; sys.path.insert(0,str(LEGACY))
from validation.bestest_pipeline import CASE_DEFINITIONS, annual_metrics, modelica_track, published_reference_tables, run_rclib_matched_forcing, run_rclib_native_solar
from validation.modelica_runner import run_validation_model
COLS=['timestamp_s','case','implementation','run_mode','formal_ashrae_result','zone_temperature_C','heating_load_W','cooling_load_W','outdoor_temperature_C','solar_gain_W']
def standard(frame,case,implementation,run_mode,solar):
    return pd.DataFrame({'timestamp_s':frame.time_s,'case':case,'implementation':implementation,'run_mode':run_mode,'formal_ashrae_result':run_mode=='native','zone_temperature_C':frame['modelica_air_temperature_c'] if implementation=='modelica' else frame['rclib_air_temperature_c'],'heating_load_W':frame['modelica_heating_w'] if implementation=='modelica' else frame['rclib_heating_w'],'cooling_load_W':frame['modelica_cooling_w'] if implementation=='modelica' else frame['rclib_cooling_w'],'outdoor_temperature_C':frame.outdoor_temperature_c,'solar_gain_W':frame[solar]})[COLS]
def metric(frame,case,implementation,run_mode):
    f=pd.DataFrame({'time_s':frame.timestamp_s,'modelica_heating_w':frame.heating_load_W,'modelica_cooling_w':frame.cooling_load_W,'rclib_heating_w':frame.heating_load_W,'rclib_cooling_w':frame.cooling_load_W}); source='Modelica' if implementation=='modelica' else 'RClib'; return annual_metrics(f,CASE_DEFINITIONS[case],source=source).assign(implementation=implementation,run_mode=run_mode,formal_ashrae_result=run_mode=='native')
def main():
    p=argparse.ArgumentParser(); p.add_argument('case',choices=('600','610','620','630','640','650','660','670','680','685','695')); p.add_argument('--run-modelica',action='store_true'); a=p.parse_args(); case=a.case; raw_path=MODEL/f'Case{case}/Case{case}_res.csv'
    if raw_path.is_file(): raw=pd.read_csv(raw_path)
    elif a.run_modelica: raw,_,_=run_validation_model(CASE_DEFINITIONS[case].modelica_class)
    else: raise FileNotFoundError(f'Missing {raw_path}; re-run with --run-modelica')
    out=ROOT/'results'/f'case{case}'; out.mkdir(parents=True,exist_ok=True); mo=modelica_track(raw); ms=standard(mo,case,'modelica','native','modelica_resolved_solar_gain_w'); (MODEL/f'Case{case}').mkdir(parents=True,exist_ok=True); ms.to_csv(MODEL/f'Case{case}/Case{case}_standardized_hourly.csv',index=False)
    nat=run_rclib_native_solar(CASE_DEFINITIONS[case],raw); ns=standard(nat,case,'iso13790','native','native_rclib_solar_gain_w'); ns.to_csv(out/f'case{case}_iso13790_native_hourly.csv',index=False)
    dia=run_rclib_matched_forcing(CASE_DEFINITIONS[case],raw); ds=standard(dia,case,'iso13790','diagnostic_modelica_solar','modelica_resolved_solar_gain_w'); ds.to_csv(out/f'case{case}_iso13790_diagnostic_modelica_solar_hourly.csv',index=False)
    allm=pd.concat([metric(ms,case,'modelica','native'),metric(ns,case,'iso13790','native'),metric(ds,case,'iso13790','diagnostic_modelica_solar')]); allm.to_csv(out/f'case{case}_metrics.csv',index=False)
    refs=published_reference_tables(); refs=refs[(refs.case==case)&refs.metric.isin(['annual_heating_energy','annual_cooling_energy'])]; form=allm[allm.run_mode.eq('native')&allm.metric.isin(refs.metric)].merge(refs[['case','metric','lower','upper']],on=['case','metric']); form['within_ashrae_range']=form.value.between(form.lower,form.upper); form.to_csv(out/f'case{case}_formal_ashrae_energy.csv',index=False)
    if case=='600':
      pd.concat([ms,ns,ds]).query('2682000 <= timestamp_s <= 2764800').to_csv(out/f'case{case}_feb1_load_profile.csv',index=False)
    solar=pd.DataFrame({'quantity':['native_rclib_zone_solar_MWh','modelica_resolved_zone_solar_MWh'],'value':[ns.solar_gain_W.sum()/1e6,ms.solar_gain_W.sum()/1e6]}); solar.loc[2]=['native_modelica_ratio',solar.value.iloc[0]/solar.value.iloc[1]]; solar.to_csv(out/f'case{case}_solar_comparison.csv',index=False)
if __name__=='__main__': main()
