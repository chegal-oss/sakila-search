from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path

import pymysql

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

config = importlib.import_module("app.config")
MYSQL_CONFIG = config.MYSQL_CONFIG
SQLITE_DB_PATH = config.SQLITE_DB_PATH

BATCH_SIZE = 1_000

TABLES = {
    "category": {
        "columns": ("category_id", "name"),
        "schema": """
            create table category (
                category_id integer primary key,
                name text not null
            )
        """,
    },
    "film": {
        "columns": (
            "film_id",
            "title",
            "language_id",
            "length",
            "release_year",
            "rating",
            "special_features",
            "description",
        ),
        "schema": """
            create table film (
                film_id integer primary key,
                title text not null,
                language_id integer not null,
                length integer,
                release_year integer,
                rating text,
                special_features text,
                description text
            )
        """,
    },
    "film_category": {
        "columns": ("film_id", "category_id"),
        "schema": """
            create table film_category (
                film_id integer not null,
                category_id integer not null,
                primary key (film_id, category_id)
            )
        """,
    },
}


def copy_table(
    mysql_connection: pymysql.connections.Connection,
    sqlite_connection: sqlite3.Connection,
    table_name: str,
) -> int:
    """Copy one configured table from MySQL to SQLite."""
    columns = TABLES[table_name]["columns"]
    mysql_columns = ", ".join(f"`{column}`" for column in columns)
    sqlite_columns = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)
    insert_query = (
        f"insert into {table_name} ({sqlite_columns}) values ({placeholders})"
    )

    copied_rows = 0
    with mysql_connection.cursor() as cursor:
        cursor.execute(f"select {mysql_columns} from `{table_name}`")
        while rows := cursor.fetchmany(BATCH_SIZE):
            sqlite_rows = [tuple(row[column] for column in columns) for row in rows]
            sqlite_connection.executemany(insert_query, sqlite_rows)
            copied_rows += len(sqlite_rows)

    return copied_rows


def create_tables(sqlite_connection: sqlite3.Connection) -> None:
    """Create SQLite tables used by the application."""
    for table_name, table in TABLES.items():
        sqlite_connection.execute(f"drop table if exists {table_name}")
        sqlite_connection.execute(table["schema"])


def copy_database(sqlite_path: Path = SQLITE_DB_PATH) -> None:
    """Copy application tables from MySQL to a local SQLite database."""
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    mysql_connection = pymysql.connect(**MYSQL_CONFIG)
    sqlite_connection = sqlite3.connect(sqlite_path)

    try:
        create_tables(sqlite_connection)
        for table_name in TABLES:
            copied_rows = copy_table(mysql_connection, sqlite_connection, table_name)
            print(f"{table_name}: {copied_rows}")
        sqlite_connection.commit()
        print(f"SQLite database created: {sqlite_path}")
    finally:
        sqlite_connection.close()
        mysql_connection.close()


if __name__ == "__main__":
    copy_database()
