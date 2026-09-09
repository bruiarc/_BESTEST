"""9XX presentation helpers, sharing metric logic with the 6XX family."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from case6xx_reporting import annual_tracks, comparison_table, peak_tracks, range_judgement

ROOT = Path(__file__).resolve().parents[1]

def prescribed_changes(case: str) -> pd.DataFrame:
    data = json.loads((ROOT / "inputs" / "case9xx_deltas.json").read_text())
    return pd.DataFrame({"case": case, "prescribed_change": data["cases"][case]["changes"] or ["Base Case 900: no delta"]})
