import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> str:
    """
    Erőforrás elérés fejlesztői és becsomagolt (PyInstaller) futásnál is.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, *parts)
    return str(PROJECT_ROOT.joinpath(*parts))
