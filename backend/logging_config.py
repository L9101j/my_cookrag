import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import settings
import sys, io
def setup_logging() -> None:
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # 控制台
    console = logging.StreamHandler(
      stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # 文件轮转
    file_handler = RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    