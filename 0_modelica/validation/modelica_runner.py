"""Run a Buildings Modelica class using the established ``run_omc.sh`` wrapper."""
from __future__ import annotations

from pathlib import Path
import os
import re
import subprocess
import tempfile

import pandas as pd

from .dependencies import VALIDATION_ROOT


MODELICA_ROOT = VALIDATION_ROOT
BUILDINGS_ROOT = MODELICA_ROOT.parents[1] / "modelica_test"
RESULTS_ROOT = BUILDINGS_ROOT / "results"


def source_file_for_class(buildings_root: Path, model_class: str) -> Path:
    """Return the upstream ``.mo`` file corresponding to ``model_class``."""
    parts = model_class.split(".")
    if not parts or parts[0] != "Buildings":
        raise ValueError("Only Buildings classes are supported")
    source = buildings_root / Path(*parts).with_suffix(".mo")
    if not source.is_file():
        raise FileNotFoundError(f"Buildings source file not found: {source}")
    return source


def _result_file_from_log(log: Path) -> Path:
    text = log.read_text(encoding="utf-8", errors="replace")
    if "Simulation Failed." in text:
        raise RuntimeError(text)
    matches = re.findall(r'resultFile\s*=\s*"([^"]*)"', text)
    if not matches or not matches[-1]:
        raise RuntimeError(f"OpenModelica returned no result file:\n{text}")
    return Path(matches[-1])


def run_modelica_class(
    root: Path, model_class: str, *, buildings_root: Path | None = None,
    output_interval_seconds: int | None = None,
) -> tuple[pd.DataFrame, Path, Path]:
    """Simulate a Buildings class and return its DataFrame, source, and CSV path."""
    root = Path(root).resolve()
    if buildings_root is None:
        buildings_root = root.parents[1] / "modelica_test"
    buildings_root = Path(buildings_root).resolve()
    source = source_file_for_class(buildings_root, model_class)
    package = buildings_root / "Buildings" / "package.mo"
    if not package.is_file():
        raise FileNotFoundError(f"Buildings package file not found: {package}")

    name = model_class.rsplit(".", 1)[-1]
    results_root = buildings_root / "results"
    result_dir = results_root / name
    result_dir.mkdir(parents=True, exist_ok=True)
    weather_name = (
        "USA_CO_Denver.Intl.AP.725650_TMY3.mos"
        if ".Validation.BESTEST." in model_class
        else "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.mos"
    )
    weather_file = buildings_root / "Buildings" / "Resources" / "weatherdata" / weather_name
    if not weather_file.is_file():
        raise FileNotFoundError(f"Buildings weather file not found: {weather_file}")
    runner_class = f"{name}NotebookRun"
    if output_interval_seconds is not None:
        output_interval_seconds = int(output_interval_seconds)
        if output_interval_seconds <= 0 or 31536000 % output_interval_seconds:
            raise ValueError("output_interval_seconds must divide one 365-day year")
        if ".Validation.BESTEST." not in model_class:
            raise ValueError("dense diagnostic output is supported for BESTEST cases only")
        simulation_options = (
            f", startTime=0, stopTime=31536000, "
            f"numberOfIntervals={31536000 // output_interval_seconds}"
        )
    else:
        simulation_options = ""
    mos = f'''loadModel(Modelica);
getErrorString();
setModelicaPath("{buildings_root}:" + getModelicaPath());
getErrorString();
loadModel(Buildings);
getErrorString();
loadString("model {runner_class}\\n  extends {model_class}(weaDat(filNam=\\\"{weather_file}\\\"));\\nend {runner_class};");
getErrorString();
cd("{result_dir}");
getErrorString();
simulate({runner_class}, outputFormat="csv", fileNamePrefix="{name}"{simulation_options});
getErrorString();
'''
    with tempfile.NamedTemporaryFile(
        "w", suffix=".mos", dir=results_root, delete=False
    ) as handle:
        handle.write(mos)
        mos_path = Path(handle.name)
    wrapper = root / "scripts" / "run_omc.sh"
    if not wrapper.is_file():
        raise FileNotFoundError(f"OpenModelica wrapper not found: {wrapper}")
    wrapper_log = results_root / mos_path.stem / "omc.log"
    try:
        completed = subprocess.run(
            ["bash", str(wrapper), str(mos_path)], cwd=root,
            env={
                **os.environ,
                "MODELICA_RESULTS_ROOT": str(results_root),
                "MODELICA_BUILDINGS_ROOT": str(buildings_root),
            },
            text=True, capture_output=True,
        )
    finally:
        mos_path.unlink(missing_ok=True)
    if completed.returncode:
        error_log = wrapper_log.with_name("omc.err")
        raise RuntimeError(error_log.read_text() if error_log.exists() else completed.stderr)
    csv_path = _result_file_from_log(wrapper_log)
    if not csv_path.is_absolute():
        csv_path = result_dir / csv_path
    if not csv_path.is_file():
        raise FileNotFoundError(f"OpenModelica reported missing CSV: {csv_path}")
    return pd.read_csv(csv_path), source, csv_path


def run_validation_model(
    model_class: str, *, buildings_root: Path | None = None,
    output_interval_seconds: int | None = None,
) -> tuple[pd.DataFrame, Path, Path]:
    """Run a model using this validation directory's bundled dependencies."""
    return run_modelica_class(
        VALIDATION_ROOT, model_class, buildings_root=buildings_root,
        output_interval_seconds=output_interval_seconds,
    )


def run_modelica_case(case: str, model_class: str) -> pd.DataFrame:
    """Run a named Buildings case and return its result table."""
    data, source, csv_path = run_modelica_class(
        MODELICA_ROOT, model_class, buildings_root=BUILDINGS_ROOT
    )
    print(f"{case}: {model_class}")
    print("Source:", source)
    print("CSV:", csv_path)
    print("Rows/columns:", data.shape)
    return data
