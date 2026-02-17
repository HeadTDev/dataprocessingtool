import os
import sys


def resource_path(*parts: str) -> str:
    """
    Erőforrás elérés fejlesztői és becsomagolt (PyInstaller) futásnál is.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, *parts)
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, *parts)
