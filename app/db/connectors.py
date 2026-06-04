from abc import ABC, abstractmethod
from typing import Generator, Any

import pymysql

from app.config import MYSQL_CONFIG
from app.logger import logger


class Connector(ABC):

    @abstractmethod
    def __enter__(self) -> Connector:
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def connect(self) -> Connector:
        pass

    @abstractmethod
    def execute(self, query: str, params: tuple | None = None) -> list[dict]:
        pass


class MySQLConnector(Connector):
    def __init__(self):
        self.__connection: pymysql.connections.Connection | None = None

    def __enter__(self) -> Connector:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Connection close")
        self.__connection.close()

    def connect(self) -> Connector:
        self.__connection = pymysql.connect(**MYSQL_CONFIG)
        logger.debug("Connection established")
        return self

    def execute(self, query: str, params = None) -> tuple[tuple[Any, ...], ...]:
        if self.__connection and self.__connection.open:
            logger.debug(f"Execute query: {query} Params: {params}")
            cursor = self.__connection.cursor()
            try:
                cursor.execute(query, params)
                return cursor.fetchall()
            finally:
                cursor.close()
        else:
            raise ValueError("Connection not established")

def connect(connection_type: type[Connector]) -> Connector:
    return connection_type()



