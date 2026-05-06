#!/usr/bin/env python3
"""Path helpers for running scripts from any working directory."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MACROPLACEMENT_ROOT = REPO_ROOT / "MacroPlacement"
PLC_CLIENT_DIR = MACROPLACEMENT_ROOT / "CodeElements" / "Plc_client"


def add_repo_paths() -> None:
    """Expose local MacroPlacement utilities to standalone scripts."""
    for path in (PLC_CLIENT_DIR, Path(__file__).resolve().parent):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
