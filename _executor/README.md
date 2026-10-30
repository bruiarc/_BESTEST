# Modelica BESTEST executor

This directory contains only the notebook and runtime needed to execute
Modelica Buildings BESTEST cases. It does not import the ISO/RClib or VDI
comparison workflows elsewhere in the repository.

## Layout

```text
_BESTEST/
├── _modelica_test_/
│   ├── Buildings/          # pinned Modelica Buildings v13.0.0 checkout
│   └── results/            # simulations and downloaded runtime dependencies
└── _executor/
    ├── _executor.ipynb
    ├── core/
    │   ├── modelica_runner.py
    │   └── run_omc.sh
    ├── requirements.txt
    └── README.md
```

## Requirements

- Python 3 with the packages in `requirements.txt`
- OpenModelica `omc`, or Docker as a fallback
- `../_modelica_test_/Buildings/package.mo`

The repository-local Buildings checkout is the default. To use another
checkout, set `MODELICA_BUILDINGS_ROOT` to a directory containing
`Buildings/package.mo`.

## Run

From the `_BESTEST` root:

```bash
python -m pip install -r _executor/requirements.txt
./_executor/core/run_omc.sh --check
cd _executor
jupyter lab _executor.ipynb
```

The notebook can also be opened from the repository root. Its setup cell
locates `_executor/core/modelica_runner.py` without relying on the process
working directory.

Simulation CSVs and runtime downloads are written under
`_modelica_test_/results/`.

## Runtime selection

The launcher uses a native `omc` executable when one is available. Set
`OPENMODELICA_OMC` when it is installed at a nonstandard path. Otherwise the
launcher uses Docker; set `DOCKER_BIN` when Docker is not on `PATH`.

The Docker fallback uses `openmodelica/openmodelica:v1.26.3-minimal` and keeps
Modelica Standard Library 4.1.0 below `_modelica_test_/results/.dependencies`.
