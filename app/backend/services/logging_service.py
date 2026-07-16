import logging
from pathlib import Path

from app.config.paths import LOGS_DIR


def configure_logging(log_name: str = "app.log") -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("dataprocessingtool")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(Path(LOGS_DIR) / log_name, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger
