from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICONS_DIR = PROJECT_ROOT / "icons"
LOGS_DIR = PROJECT_ROOT / "logs"


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


def module_output_dir(module_name: str) -> Path:
    output_dir = PROJECT_ROOT / "output" / module_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
