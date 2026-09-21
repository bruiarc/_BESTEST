"""Generate the compact VDI BESTEST notebook suite from centralized helpers."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

NAMES = {
    "600":"01_case600_validation.ipynb", "610":"01a_case610_validation.ipynb",
    "620":"01b_case620_validation.ipynb", "630":"01c_case630_validation.ipynb",
    "640":"01d_case640_validation.ipynb", "650":"01e_case650_validation.ipynb",
    "660":"01f_case660_validation.ipynb", "670":"01g_case670_validation.ipynb",
    "680":"01h_case680_validation.ipynb", "685":"01i_case685_validation.ipynb",
    "695":"01j_case695_validation.ipynb", "900":"02_case900_validation_clean.ipynb",
    "910":"02a_case910_validation.ipynb", "920":"02b_case920_validation.ipynb",
    "930":"02c_case930_validation.ipynb", "940":"02d_case940_validation.ipynb",
    "950":"02e_case950_validation.ipynb", "980":"02f_case980_validation.ipynb",
    "985":"02g_case985_validation.ipynb", "995":"02h_case995_validation.ipynb",
}


def md(text): return {"cell_type":"markdown", "metadata":{}, "source":[text]}
def code(text): return {"cell_type":"code", "execution_count":None, "metadata":{}, "outputs":[], "source":[text]}
def notebook(cells):
    return {"cells":cells, "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python","version":"3"}}, "nbformat":4, "nbformat_minor":5}


for case, name in NAMES.items():
    cells = [
        md(f"# BESTEST Case {case} — VDI 6007 validation"),
        code("from doc.bestest_vdi_reporting import (case_definition, resolved_input_mapping, static_checks, annual_validation, parent_response)\nCASE = \"%s\"" % case),
        md("## Case definition and provenance"), code("case_definition(CASE)"),
        md("## Resolved VDI input mapping"), code("resolved_input_mapping(CASE)"),
        md("## Static validation checks"), code("static_checks(CASE)"),
        md("## Annual heating and cooling against benchmark bounds"), code("annual_validation(CASE)"),
        md("## Parent-relative interpretation"), code("parent_response(CASE)"),
    ]
    (ROOT / name).write_text(json.dumps(notebook(cells), indent=1) + "\n")

summaries = {
    "01_cases6xx_summary.ipynb": ("BESTEST 6XX — VDI 6007 summary", "family_summary('6xx')"),
    "02_cases9xx_summary.ipynb": ("BESTEST 9XX — VDI 6007 summary", "family_summary('9xx')"),
    "03_bestest_vdi_summary.ipynb": ("BESTEST 6XX and 9XX — VDI 6007 summary", "combined_summary()"),
}
for name, (title, expression) in summaries.items():
    cells = [md(f"# {title}"),
        code("from doc.bestest_vdi_reporting import family_summary, combined_summary, unresolved_benchmark_issues"),
        md("## Annual benchmark and parent-relative response"), code(expression),
        md("## Unresolved benchmark-data issues"), code("unresolved_benchmark_issues()")]
    (ROOT / name).write_text(json.dumps(notebook(cells), indent=1) + "\n")
