import logging
import sys
from pathlib import Path

formatter = "%(asctime)s - %(filename)s - %(levelname)s - %(lineno)d - %(message)s"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter(formatter))
log_path = Path(__file__).resolve().parent.parent / "logs" / "app.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(formatter))

logger.addHandler(console_handler)
logger.addHandler(file_handler)



