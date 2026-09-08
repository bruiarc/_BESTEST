"""Shared 6XX prescribed-delta and report helpers; notebooks contain no model logic."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def prescribed_changes(case: str) -> pd.DataFrame:
    data=json.loads((ROOT/'inputs/case6xx_deltas.json').read_text())
    return pd.DataFrame({'case':case,'prescribed_change':data['cases'][case]['changes'] or ['Base Case 600: no delta']})
