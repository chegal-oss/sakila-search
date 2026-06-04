from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from app.logger import logger

from .connector import Connector
from .model import Category, Film, Period, UserQuery

if TYPE_CHECKING:
    from .history import HistoryConnector


class SakilaRepo:
    """Repository for film search data and optional search-history storage."""

    FILMS_ON_PAGE = 10

    def __init__(self, connector: Connector, history: HistoryConnector | None = None):
        """Create a repository from SQL connector and optional history storage."""
        self.__connector: Connector = connector
        self.__history = history
        self.current_page: int = 0

    def get_films(
        self,
        category_id: int | None = None,
        years: str | None = None,
        search_title: str | None = None,
    ) -> Generator[Film]:
        """Yield films filtered by category, release-year period and title."""
        where_parts: list[str] = []
        query_params: list[int | str] = []

        if category_id:
            where_parts.append("and c.category_id = ?")
            query_params.append(category_id)

        if years:
            start_year, end_year = years.split("-")
            where_parts.append("and f.release_year between ? and ?")
            query_params.extend([int(start_year), int(end_year)])

        if search_title:
            where_parts.append("and lower(f.title) like ?")
            query_params.append(f"%{search_title.lower()}%")

        where_statement = " ".join(where_parts)
        offset = self.current_page * self.FILMS_ON_PAGE
        query_params.extend([self.FILMS_ON_PAGE, offset])
        logger.info(
            "Fetching films: category_id=%s, years=%s, search=%s, offset=%s, limit=%s",
            category_id,
            years,
            search_title or "All",
            offset,
            self.FILMS_ON_PAGE,
        )
        rows = self.__connector.execute(
            Film.get_query(where_statement), tuple(query_params)
        )
        logger.info("Films fetched: %s", len(rows))
        yield from map(Film.from_dict, rows)

    def get_category(self) -> Generator[Category]:
        """Yield all film categories with the synthetic 'All' option."""
        yield from map(
            Category.from_dict, self.__connector.execute(Category.get_query())
        )

    def get_year(self) -> Generator[Period]:
        """Yield available release-year periods with the synthetic 'All' option."""
        rows = self.__connector.execute(Period.get_query())
        yield from Period.from_release_years(rows)

    def save_query(self, query: UserQuery) -> None:
        """Persist a search query when history storage is configured."""
        if self.__history is None:
            return
        self.__history.save_query(query)

    def get_popular_queries(self, limit: int = 5) -> list[UserQuery]:
        """Return the most frequently used search queries from history."""
        if self.__history is None:
            return []
        return self.__history.get_popular_queries(limit)
