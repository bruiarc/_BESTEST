# Modelica BESTEST executor

Run annual ISO 13790 BESTEST simulations from the repository-local Modelica
Buildings Library.

## Requirements

- [ ] Python 3
- [ ] Python packages from `requirements.txt`
- [ ] OpenModelica `omc`, or Docker
- [ ] `../modelica_test/Buildings/package.mo`
- [ ] Denver TMY3 weather file in `../modelica_test/Buildings/Resources/weatherdata`
- [ ] `_executor.ipynb`
- [ ] `_validation/`

## Create `modelica_test` from scratch with Git

Run these commands from the `_BESTEST` repository root. They create a shallow,
version-pinned checkout of the official Modelica Buildings Library and a local
results directory:

```bash
git clone --branch v13.0.0 --depth 1 \
  https://github.com/lbl-srg/modelica-buildings.git modelica_test
mkdir -p modelica_test/results
test -f modelica_test/Buildings/package.mo
```

The final command exits successfully when the expected package is present. The
checkout is intentionally excluded by this repository's `.gitignore`; it is an
external dependency rather than project source. Pinning `v13.0.0` makes the
setup reproducible and matches the OpenModelica 1.26.3 runtime used by the
Docker route. To replace an existing checkout, move or remove it first rather
than cloning over it.

## Repository tree

```text
repository/
├── modelica_test/
│   ├── Buildings/                 # downloaded Modelica Buildings Library
│   ├── results/                   # all generated simulations and dependencies
│   └── README.md                  # clean-download instructions
└── _BESTEST/_modelica/
    ├── _executor.ipynb
    ├── _validation/              # validation and execution code
    │   └── run_omc.sh            # OpenModelica launcher
    ├── requirements.txt
    └── README.md
```

## Modelica configuration

`_executor.ipynb` is a Modelica-only executor. It does not import or require
`RC_br/RClib`. It calls `_validation/modelica_runner.py`, which creates a
temporary OpenModelica script (`.mos`) for each requested BESTEST model. The
Python runner passes that file and the required library and results paths to
`_validation/run_omc.sh`. The launcher runs the simulation and the Python code
loads the resulting CSV file.

Choose one of the following configurations.

### (1) Run OpenModelica directly

Install [OpenModelica](https://openmodelica.org/download/) and confirm that its
`omc` executable is on `PATH`:

```bash
omc --version
```

If `omc` is installed in a nonstandard location, configure the launcher with
its absolute path before starting Jupyter:

```bash
export OPENMODELICA_OMC=/absolute/path/to/omc
```

From the repository root, verify that `run_omc.sh` selects the native runtime:

```bash
./_modelica/_validation/run_omc.sh --check
```

The output should identify the path to the native `omc` executable. Then start
the notebook from the `_modelica` directory so that its local `_validation`
package is importable:

```bash
cd _modelica
jupyter lab _executor.ipynb
```

Run the notebook cells from top to bottom. The first code cell defines `CASES`;
edit that mapping if only selected cases should run. The second code cell calls
`run_modelica_case` for every entry and displays the shape of each returned
result table.

### (2) Run OpenModelica through Docker (alternative, untested)

Use this configuration when a native `omc` executable is not installed. On
macOS, install and start Docker Desktop:

```bash
brew install --cask docker
open -a Docker
```

The launcher finds the Docker CLI on `PATH` or in Docker Desktop's standard
macOS location. If necessary, configure another location before starting
Jupyter:

```bash
export DOCKER_BIN=/absolute/path/to/docker
```

Verify that Docker is running and selected:

```bash
./_modelica/_validation/run_omc.sh --check
```

Then operate `_executor.ipynb` in the same way:

```bash
cd _modelica
jupyter lab _executor.ipynb
```

Run the cells from top to bottom and edit `CASES` when a different selection is
required. Docker uses the `openmodelica/openmodelica:v1.26.3-minimal` image and
mounts the project, result, and Buildings Library directories into the
container. On its first run, the launcher also downloads Modelica Standard
Library 4.1.0 into the results dependency cache. This Docker route is provided
as an alternative but has not yet been validated in this workspace.

In both configurations, the Python runner resolves the Buildings checkout and
passes `MODELICA_RESULTS_ROOT` and `MODELICA_BUILDINGS_ROOT` to `run_omc.sh`
automatically. Simulation output and the `omc.log` and `omc.err` diagnostic
files are written below the resolved results directory. If native `omc` and
Docker are both available, `run_omc.sh` uses the native executable. Neither
route depends on whether Jupyter is launched from
the repository root, `_modelica`, or one of their subdirectories because
`_executor.ipynb` locates `_modelica` before importing the runner. The
runner looks for `modelica_test` in the current repository layout. On another
computer or with a different layout, set the portable configuration explicitly
before starting Jupyter:

```bash
export MODELICA_BUILDINGS_ROOT=/absolute/path/to/modelica_test
```

That directory must contain `Buildings/package.mo` and the Buildings weather
files. The same setting can be entered in the configuration cell in
`_executor.ipynb`. Paths to `omc` or Docker only need to be supplied when those
executables cannot be found in their standard locations.
