"""Resolve validation dependencies from the current workspace layout."""
from __future__ import annotations

from pathlib import Path
import sys


VALIDATION_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
RCLIB_PARENT = WORKSPACE_ROOT / "RC_br"


def _ensure_rclib_importable() -> None:
    """Expose ``RC_br/RClib`` without depending on the process cwd."""
    package = RCLIB_PARENT / "RClib" / "__init__.py"
    if not package.is_file():
        raise ModuleNotFoundError(
            "The validation requires RC_br/RClib; expected it at "
            f"{package.parent}"
        )
    parent = str(RCLIB_PARENT)
    if parent not in sys.path:
        sys.path.insert(0, parent)


def zone_class():
    """Return the authoritative ISO 13790 ``Zone`` class."""
    _ensure_rclib_importable()
    from RClib.iso13790 import Zone

    return Zone


def radiation_classes():
    """Return the authoritative ISO 13790 radiation classes."""
    _ensure_rclib_importable()
    from RClib.iso13790.radiation import Location, OpaqueSurface, Window

    return Location, Window, OpaqueSurface

