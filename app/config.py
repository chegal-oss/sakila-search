import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
LOG_FILE_PATH = APP_DIR / "logs" / "app.log"
SQLITE_DB_PATH = BASE_DIR / "data" / "sakila.sqlite"


def _get_env(name: str, default: str) -> str:
    """Return an environment value or a safe default for standalone imports."""
    return os.getenv(name) or default


MYSQL_CONFIG = {
    "host": _get_env("DB_HOST", "localhost"),
    "port": int(_get_env("DB_PORT", "3306")),
    "user": _get_env("DB_USER", "root"),
    "password": _get_env("DB_PASSWORD", ""),
    "database": _get_env("DB_NAME", "sakila"),
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": int(_get_env("DB_CONNECT_TIMEOUT", "3")),
}

MONGO_URI = _get_env("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = _get_env("MONGO_DATABASE", "sakila_films")
MONGO_COLLECTION = _get_env("MONGO_COLLECTION", "queries")
MONGO_TIMEOUT_MS = int(_get_env("MONGO_TIMEOUT_MS", "3000"))
