#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OMC_BIN="${OPENMODELICA_OMC:-}"
DOCKER_BIN="${DOCKER_BIN:-}"

if [[ -z "$OMC_BIN" ]] && command -v omc >/dev/null 2>&1; then
  OMC_BIN="$(command -v omc)"
fi
if [[ -z "$DOCKER_BIN" ]] && command -v docker >/dev/null 2>&1; then
  DOCKER_BIN="$(command -v docker)"
elif [[ -z "$DOCKER_BIN" ]] && [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
  DOCKER_BIN=/Applications/Docker.app/Contents/Resources/bin/docker
fi

if [[ -z "$OMC_BIN" && -z "$DOCKER_BIN" ]]; then
  cat >&2 <<'EOF'
No Modelica runtime was found.

Install one of the following, then restart Jupyter:
  - Docker Desktop: https://www.docker.com/products/docker-desktop/
  - OpenModelica:   https://openmodelica.org/download/

On macOS with Homebrew:
  brew install --cask docker
  open -a Docker

If already installed in a nonstandard location, set OPENMODELICA_OMC or DOCKER_BIN.
EOF
  exit 127
fi

if [[ "${1:-}" == "--check" ]]; then
  if [[ -n "$OMC_BIN" ]]; then
    echo "Modelica runtime: $OMC_BIN"
  else
    if ! "$DOCKER_BIN" info >/dev/null 2>&1; then
      echo "Docker was found at $DOCKER_BIN, but its daemon is not running. Start Docker Desktop and retry." >&2
      exit 125
    fi
    echo "Modelica runtime: Docker ($DOCKER_BIN)"
  fi
  exit 0
fi

MOS_FILE="${1:?usage: run_omc.sh MOS_FILE | --check}"
if [[ "$MOS_FILE" = /* ]]; then
  MOS_PATH="$MOS_FILE"
else
  MOS_PATH="$ROOT/$MOS_FILE"
fi
RESULTS_ROOT="${MODELICA_RESULTS_ROOT:?MODELICA_RESULTS_ROOT must be set}"
BUILDINGS_ROOT="${MODELICA_BUILDINGS_ROOT:?MODELICA_BUILDINGS_ROOT must be set}"

if [[ ! -f "$MOS_PATH" ]]; then
  echo "MOS file not found: $MOS_PATH" >&2
  exit 2
fi

NAME="$(basename "$MOS_FILE" .mos)"
OUT_DIR="$RESULTS_ROOT/$NAME"
mkdir -p "$OUT_DIR"

if [[ -n "$OMC_BIN" ]]; then
  (cd "$OUT_DIR" && "$OMC_BIN" "$MOS_PATH") >"$OUT_DIR/omc.log" 2>"$OUT_DIR/omc.err"
else
  MSL_VERSION="4.1.0"
  DEPENDENCY_DIR="$RESULTS_ROOT/.dependencies"
  MSL_ROOT="$DEPENDENCY_DIR/ModelicaStandardLibrary-$MSL_VERSION"
  if [[ ! -f "$MSL_ROOT/Modelica/package.mo" ]]; then
    ARCHIVE="$DEPENDENCY_DIR/ModelicaStandardLibrary-$MSL_VERSION.tar.gz"
    mkdir -p "$DEPENDENCY_DIR"
    curl -fL \
      "https://github.com/modelica/ModelicaStandardLibrary/archive/refs/tags/v$MSL_VERSION.tar.gz" \
      -o "$ARCHIVE"
    tar -xzf "$ARCHIVE" -C "$DEPENDENCY_DIR"
  fi
  LIBRARY_PATH="$MSL_ROOT:$BUILDINGS_ROOT"
  "$DOCKER_BIN" run --rm \
    -v "$ROOT:$ROOT" \
    -v "$RESULTS_ROOT:$RESULTS_ROOT" \
    -v "$BUILDINGS_ROOT:$BUILDINGS_ROOT:ro" \
    -e "MODELICAPATH=$LIBRARY_PATH" \
    -e "OPENMODELICALIBRARY=$LIBRARY_PATH" \
    -w "$OUT_DIR" \
    --user "$(id -u):$(id -g)" \
    openmodelica/openmodelica:v1.26.3-minimal \
    omc "$MOS_PATH" >"$OUT_DIR/omc.log" 2>"$OUT_DIR/omc.err"
fi
