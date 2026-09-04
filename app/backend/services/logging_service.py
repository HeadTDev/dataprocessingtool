import sys

from loguru import logger as _logger

from app.config.paths import module_log_dir
from app.config.settings import DEBUG

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[module]} | "
    "{name}:{function}:{line} - {message}"
)
_CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{extra[module]}</cyan> - <level>{message}</level>"
)

_logger.remove()
if DEBUG:
    _logger.add(sys.stderr, level="DEBUG", format=_CONSOLE_FORMAT, colorize=True)

_configured_modules: set[str] = set()


def get_logger(module_name: str):
    """Visszaad egy, a modulhoz kötött loggert.

    Minden modul saját mappát és forgó (rotálódó) logfájlt kap a logs/ alatt
    (pl. logs/ksh/ksh.log), így egy modul hibái mindig külön nyomon
    követhetők a többitől. A fájlba írt logok sosem tartalmazhatnak
    feldolgozott céges adatot (cégnév, összeg, stb.) - csak folyamat-
    eseményeket, számokat és hibaüzeneteket.
    """
    if module_name not in _configured_modules:
        log_dir = module_log_dir(module_name)
        _logger.add(
            log_dir / f"{module_name}.log",
            level="DEBUG",
            format=_FILE_FORMAT,
            rotation="5 MB",
            retention=5,
            compression="zip",
            encoding="utf-8",
            enqueue=True,
            filter=lambda record, _module=module_name: record["extra"].get("module") == _module,
        )
        _configured_modules.add(module_name)
    return _logger.bind(module=module_name)


# Visszafelé kompatibilis, egyszerű app-szintű logger (pl. main.py indítási eseményeihez)
def configure_logging(module_name: str = "app"):
    return get_logger(module_name)
