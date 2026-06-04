from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pymysql

from app.config import MYSQL_CONFIG, SQLITE_DB_PATH
from app.logger import logger

SQLParams = tuple[Any, ...] | None


class Connector(ABC):
    """Abstract database connector interface used by repositories."""

    @abstractmethod
    def __enter__(self) -> Connector:
        """Open the connector for usage in a context manager."""

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the connector when leaving a context manager."""

    @abstractmethod
    def connect(self) -> Connector:
        """Establish a database connection and return the connector."""

    @abstractmethod
    def execute(self, query: str, params: SQLParams = None) -> list[dict[str, Any]]:
        """Execute a SQL query and return rows as dictionaries."""

    def prepare_query(self, query: str) -> str:
        """Return a query adapted to the connector's database driver."""
        return query


class MySQLConnector(Connector):
    """PyMySQL implementation of the application database connector."""

    def __init__(self):
        """Create an empty connector without opening a database connection."""
        self.__connection: pymysql.connections.Connection | None = None

    def __enter__(self) -> Connector:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        logger.debug("Connection close")
        if self.__connection:
            self.__connection.close()

    def connect(self) -> Connector:
        self.__connection = pymysql.connect(**MYSQL_CONFIG)
        logger.debug("Connection established")
        return self

    def execute(self, query: str, params: SQLParams = None) -> list[dict[str, Any]]:
        """Execute a query against MySQL using optional bound parameters."""
        if self.__connection and self.__connection.open:
            prepared_query = self.prepare_query(query)
            logger.debug("Execute query: %s Params: %s", prepared_query, params)
            cursor = self.__connection.cursor()
            try:
                cursor.execute(prepared_query, params)
                return cursor.fetchall()
            finally:
                cursor.close()
        else:
            raise ValueError("Connection not established")

    def prepare_query(self, query: str) -> str:
        """Convert SQLite-style placeholders to PyMySQL placeholders."""
        return query.replace("?", "%s")


class SQLiteConnector(Connector):
    """sqlite3 implementation of the application database connector."""

    def __init__(self, database_path: Path = SQLITE_DB_PATH):
        """Create an empty connector for a local SQLite database file."""
        self.__database_path = database_path
        self.__connection: sqlite3.Connection | None = None

    def __enter__(self) -> Connector:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        logger.debug("SQLite connection close")
        if self.__connection:
            self.__connection.close()

    def connect(self) -> Connector:
        if not self.__database_path.exists():
            raise FileNotFoundError(
                f"SQLite database not found: {self.__database_path}. "
                "Run scripts/copy_mysql_to_sqlite.py first."
            )
        self.__connection = sqlite3.connect(self.__database_path)
        self.__connection.row_factory = sqlite3.Row
        logger.debug("SQLite connection established: %s", self.__database_path)
        return self

    def execute(self, query: str, params: SQLParams = None) -> list[dict[str, Any]]:
        """Execute a query against SQLite using optional bound parameters."""
        if self.__connection is None:
            raise ValueError("Connection not established")

        prepared_query = self.prepare_query(query)
        logger.debug("Execute query: %s Params: %s", prepared_query, params)
        cursor = self.__connection.cursor()
        try:
            cursor.execute(prepared_query, params or ())
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()


class FallbackConnector(Connector):
    """Connector that uses MySQL first and falls back to local SQLite."""

    def __init__(self):
        """Create an unopened fallback connector."""
        self.__connector: Connector | None = None

    def __enter__(self) -> Connector:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        logger.debug("Fallback connection close")
        if self.__connector:
            self.__connector.__exit__(exc_type, exc_val, exc_tb)

    def connect(self) -> Connector:
        try:
            self.__connector = MySQLConnector().connect()
        except Exception as exc:
            logger.warning("MySQL is unavailable, fallback to local SQLite: %s", exc)
            self.__connector = SQLiteConnector().connect()
        return self

    def execute(self, query: str, params: SQLParams = None) -> list[dict[str, Any]]:
        """Execute a query using the opened concrete connector."""
        if self.__connector is None:
            raise ValueError("Connection not established")
        return self.__connector.execute(query, params)


def connect(connection_type: type[Connector]) -> Connector:
    """Create a connector instance for the requested connector type."""
    return connection_type()
