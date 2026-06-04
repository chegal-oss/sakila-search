from __future__ import annotations

from datetime import datetime, UTC

from pymongo import DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.config import MONGO_COLLECTION, MONGO_DATABASE, MONGO_URI
from app.db.model import UserQuery
from app.logger import logger


class MongoHistoryConnector:
    def __init__(self):
        self._client: MongoClient | None = None
        self._collection: Collection | None = None

    def __enter__(self) -> MongoHistoryConnector:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def connect(self) -> MongoHistoryConnector:
        if self._client is not None:
            return self

        self._client = MongoClient(MONGO_URI)
        self._collection = self._client[MONGO_DATABASE][MONGO_COLLECTION]
        try:
            self._collection.create_index([("query", DESCENDING), ("searched_at", DESCENDING)])
        except PyMongoError:
            pass
        return self

    def close(self):
        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._collection = None

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self.connect()
        return self._collection

    def save_query(self, query: UserQuery) -> None:

        try:
            self.collection.insert_one({"query": query.to_dict(), "searched_at": datetime.now(UTC)})
            logger.debug("Search query saved: %s", query)
        except PyMongoError as e:
            logger.debug("Search query was not saved: %s", e)
            return

    def get_popular_queries(self, limit: int = 5) -> list[UserQuery]:
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
        try:
            self.collection.delete_many({})
        except PyMongoError:
            return

def connect():
    return MongoHistoryConnector().connect()
