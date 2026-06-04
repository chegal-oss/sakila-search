from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from pymongo import DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.config import (
    MONGO_COLLECTION,
    MONGO_DATABASE,
    MONGO_TIMEOUT_MS,
    MONGO_URI,
    SQLITE_DB_PATH,
)
from app.db.model import UserQuery
from app.logger import logger


class HistoryConnector(ABC):
    """Abstract search-history storage interface."""

    @abstractmethod
    def __enter__(self) -> HistoryConnector:
        """Open history storage for context-manager usage."""

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close history storage after context-manager usage."""

    @abstractmethod
    def connect(self) -> HistoryConnector:
        """Connect to history storage and return the connector."""

    @abstractmethod
    def close(self) -> None:
        """Close history storage."""

    @abstractmethod
    def save_query(self, query: UserQuery) -> None:
        """Save a single user search query."""

    @abstractmethod
    def get_popular_queries(self, limit: int = 5) -> list[UserQuery]:
        """Return the most frequently searched queries."""

    @abstractmethod
    def clear_queries(self) -> None:
        """Delete all stored search queries."""


class MongoHistoryConnector(HistoryConnector):
    """MongoDB connector responsible for storing and reading search history."""

    def __init__(self):
        """Create an empty history connector without opening MongoDB yet."""
        self._client: MongoClient | None = None
        self._collection: Collection | None = None

    def __enter__(self) -> HistoryConnector:
        """Open the MongoDB connection for context-manager usage."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the MongoDB connection when leaving a context manager."""
        self.close()

    def connect(self) -> HistoryConnector:
        """Connect to MongoDB and prepare indexes for search history."""
        if self._client is not None:
            return self

        self._client = MongoClient(
            MONGO_URI,
            connectTimeoutMS=MONGO_TIMEOUT_MS,
            serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
            socketTimeoutMS=MONGO_TIMEOUT_MS,
        )
        self._client.admin.command("ping")
        self._collection = self._client[MONGO_DATABASE][MONGO_COLLECTION]
        with suppress(PyMongoError):
            self._collection.create_index(
                [("query", DESCENDING), ("searched_at", DESCENDING)]
            )
        return self

    def close(self) -> None:
        """Close the active MongoDB client if it exists."""
        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._collection = None

    @property
    def collection(self) -> Collection:
        """Return the configured MongoDB collection, connecting lazily if needed."""
        if self._collection is None:
            self.connect()
        assert self._collection is not None
        return self._collection

    def save_query(self, query: UserQuery) -> None:
        """Save a single user search query to MongoDB."""

        try:
            self.collection.insert_one(
                {"query": query.to_dict(), "searched_at": datetime.now(UTC)}
            )
            logger.debug("Search query saved: %s", query)
        except PyMongoError as e:
            logger.debug("Search query was not saved: %s", e)
            return

    def get_popular_queries(self, limit: int = 5) -> list[UserQuery]:
        """Return the most frequently searched queries from MongoDB."""
        try:
            items = self.collection.aggregate(
                [
                    {"$match": {"query": {"$exists": True, "$type": "object"}}},
                    {
                        "$group": {
                            "_id": "$query",
                            "count": {"$sum": 1},
                            "last_searched_at": {"$max": "$searched_at"},
                        }
                    },
                    {"$sort": {"count": -1, "last_searched_at": -1}},
                    {"$limit": limit},
                ]
            )
            popular_queries: list[UserQuery] = []
            for item in items:
                query = UserQuery.from_dict(item)
                if query:
                    popular_queries.append(query)
            return popular_queries
        except PyMongoError:
            return []

    def clear_queries(self) -> None:
        """Delete all stored search queries."""
        try:
            self.collection.delete_many({})
        except PyMongoError:
            return


class SQLiteHistoryConnector(HistoryConnector):
    """SQLite connector responsible for local search-history storage."""

    def __init__(self, database_path: Path = SQLITE_DB_PATH):
        """Create an unopened SQLite history connector."""
        self._database_path = database_path
        self._connection: sqlite3.Connection | None = None

    def __enter__(self) -> HistoryConnector:
        """Open SQLite history storage for context-manager usage."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close SQLite history storage after context-manager usage."""
        self.close()

    def connect(self) -> HistoryConnector:
        """Connect to SQLite and prepare the search-history table."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            """
            create table if not exists search_history (
                id integer primary key autoincrement,
                category_id integer not null,
                category_name text not null,
                period_id integer not null,
                period text not null,
                title text not null,
                searched_at text not null
            )
            """
        )
        self._connection.commit()
        return self

    def close(self) -> None:
        """Close the active SQLite connection if it exists."""
        if self._connection is None:
            return
        self._connection.close()
        self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the active SQLite connection."""
        if self._connection is None:
            self.connect()
        assert self._connection is not None
        return self._connection

    def save_query(self, query: UserQuery) -> None:
        """Save a single user search query to SQLite."""
        data = query.to_dict()
        category = data["category"]
        years = data["years"]
        self.connection.execute(
            """
            insert into search_history (
                category_id, category_name, period_id, period, title, searched_at
            )
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                category["id"],
                category["name"],
                years["id"],
                years["period"],
                data["title"],
                datetime.now(UTC).isoformat(),
            ),
        )
        self.connection.commit()

    def get_popular_queries(self, limit: int = 5) -> list[UserQuery]:
        """Return the most frequently searched queries from SQLite."""
        rows = self.connection.execute(
            """
            select
                category_id,
                category_name,
                period_id,
                period,
                title,
                count(*) as count,
                max(searched_at) as last_searched_at
            from search_history
            group by category_id, category_name, period_id, period, title
            order by count desc, last_searched_at desc
            limit ?
            """,
            (limit,),
        ).fetchall()

        queries = []
        for row in rows:
            queries.append(
                UserQuery.from_dict(
                    {
                        "query": {
                            "category": {
                                "id": row["category_id"],
                                "name": row["category_name"],
                            },
                            "years": {"id": row["period_id"], "period": row["period"]},
                            "title": row["title"],
                        },
                        "count": row["count"],
                        "last_searched_at": datetime.fromisoformat(
                            row["last_searched_at"]
                        ),
                    }
                )
            )
        return [query for query in queries if query]

    def clear_queries(self) -> None:
        """Delete all stored search queries from SQLite."""
        self.connection.execute("delete from search_history")
        self.connection.commit()


class FallbackHistoryConnector(HistoryConnector):
    """History connector that uses MongoDB first and falls back to SQLite."""

    def __init__(self):
        """Create an unopened fallback history connector."""
        self._connector: HistoryConnector | None = None

    def __enter__(self) -> HistoryConnector:
        """Open MongoDB first, or SQLite when MongoDB is unavailable."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the opened history connector."""
        self.close()

    def connect(self) -> HistoryConnector:
        """Connect to MongoDB or fallback to local SQLite."""
        try:
            self._connector = MongoHistoryConnector().connect()
        except Exception as exc:
            logger.warning(
                "MongoDB is unavailable, fallback to local SQLite history: %s", exc
            )
            self._connector = SQLiteHistoryConnector().connect()
        return self

    def close(self) -> None:
        """Close the active history connector if it exists."""
        if self._connector:
            self._connector.close()
            self._connector = None

    def save_query(self, query: UserQuery) -> None:
        """Save a single user search query using the opened connector."""
        if self._connector is None:
            raise ValueError("History connection not established")
        self._connector.save_query(query)

    def get_popular_queries(self, limit: int = 5) -> list[UserQuery]:
        """Return popular queries using the opened connector."""
        if self._connector is None:
            raise ValueError("History connection not established")
        return self._connector.get_popular_queries(limit)

    def clear_queries(self) -> None:
        """Delete all stored search queries using the opened connector."""
        if self._connector is None:
            raise ValueError("History connection not established")
        self._connector.clear_queries()
