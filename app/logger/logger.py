import logging
import sys

from app.config import LOG_FILE_PATH

formatter = "%(asctime)s - %(filename)s - %(levelname)s - %(lineno)d - %(message)s"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter(formatter))
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(LOG_FILE_PATH, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(formatter))

logger.addHandler(console_handler)
logger.addHandler(file_handler)
