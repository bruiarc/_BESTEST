# Modelica BESTEST executor

Run annual ISO 13790 BESTEST simulations from the repository-local Modelica
Buildings Library.

## Requirements

- [ ] Python 3
- [ ] Python packages from `requirements.txt`
- [ ] OpenModelica `omc`, or Docker
- [ ] `../../modelica_test/Buildings/package.mo`
- [ ] Denver TMY3 weather file in `../../modelica_test/Buildings/Resources/weatherdata`
- [ ] `modelica_executor.ipynb`
- [ ] `iso_validation/`

The external library is already stored in [`../../modelica_test`](../../modelica_test).
Its README explains how to download a clean replacement from the web.

## Repository tree

```text
repository/
├── modelica_test/
│   ├── Buildings/                 # downloaded Modelica Buildings Library
│   ├── results/                   # all generated simulations and dependencies
│   └── README.md                  # clean-download instructions
└── _BESTEST/0_modelica/
    ├── modelica_bestest_executor.ipynb
    ├── iso_validation/           # Python execution code
    ├── scripts/run_omc.sh        # omc/Docker launcher
    ├── requirements.txt
    └── README.md
```

Install and start a Modelica runtime before opening the notebook. Docker
Desktop is the simplest option on macOS:

```bash
brew install --cask docker
open -a Docker
_BESTEST/0_modelica/scripts/run_omc.sh --check
```

Alternatively, install OpenModelica from <https://openmodelica.org/download/>.
For a nonstandard executable location, set `DOCKER_BIN` or
`OPENMODELICA_OMC` before starting Jupyter.

## Setup

Run from the repository directory:

```bash
python3 -m venv _BESTEST/0_modelica/.venv
_BESTEST/0_modelica/.venv/bin/python -m pip install \
  -r _BESTEST/0_modelica/requirements.txt
```

## Run

```bash
_BESTEST/0_modelica/.venv/bin/python -m jupyter lab \
  _BESTEST/0_modelica/modelica_bestest_executor.ipynb
```

All generated simulations, logs, executables, and downloaded Modelica Standard
Library dependencies are kept together in:

```text
modelica_test/results/<case>/
```
