from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar


@dataclass()
class Record:
    """Base record mapped from a database row."""

    SQL_QUERY: ClassVar[str] = ""

    @classmethod
    def get_query(cls, where_statement: str = None) -> str:
        """Return the SQL query for this record type."""
        return cls.SQL_QUERY.format(where_statement=where_statement or "")

    @classmethod
    def from_dict(cls, dict_item: dict):
        """Build a dataclass instance from a database row dictionary."""
        return cls(**dict_item)


@dataclass
class Film(Record):
    """Film row returned by the Sakila film search query."""

    SQL_QUERY = """
        select
            f.film_id,
            f.title,
            f.language_id,
            f.length,
            f.release_year,
            c.name as category,
            f.rating,
            f.special_features,
            f.description
        from film as f
             inner join film_category as fc on fc.film_id = f.film_id
             inner join category as c on fc.category_id = c.category_id
        where 1 {where_statement}
        order by f.release_year, f.title
        limit ? offset ?
        """

    film_id: int
    title: str
    language_id: int
    length: int
    release_year: int
    category: str
    rating: str
    special_features: str | None = None
    description: str | None = None

    def __str__(self):
        """Format film data for CLI output."""
        return (
            f"{self.title:30} {self.release_year:^26} {self.category:20} {self.rating}"
        )


@dataclass
class Category(Record):
    """Film category filter option."""

    POPULAR: ClassVar[int] = -1
    ALL: ClassVar[int] = 0
    SQL_QUERY = """
        select category_id, name from category
        union select 0 as category_id, 'All' as name
        order by category_id
    """
    category_id: int
    name: str


@dataclass
class Period(Record):
    """Release-year period filter option."""

    SQL_QUERY = """
        select distinct release_year
        from film
        order by release_year
    """

    id: int
    period: str

    @classmethod
    def from_release_years(cls, rows: Iterable[dict[str, Any]]) -> list[Period]:
        """Build five-year periods from film release years."""
        buckets: dict[int, list[int]] = {}

        for row in rows:
            year = int(row["release_year"])
            bucket = (year - 1) // 5
            buckets.setdefault(bucket, []).append(year)

        periods = [Period(0, "All")]
        for years in buckets.values():
            start_year = min(years)
            end_year = max(years)
            periods.append(Period(start_year, f"{start_year}-{end_year}"))
        return periods


@dataclass
class UserQuery:
    """User-selected film search filters saved in history."""

    category: Category | None = None
    years: Period | None = None
    title: str | None = None
    count: int | None = None
    last_searched_at: datetime | None = None

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> UserQuery | None:
        """Build a search query from a MongoDB aggregation item."""
        query = item.get("_id") or item.get("query")
        if not isinstance(query, dict):
            return None

        category = query.get("category") or {}
        years = query.get("years") or {}

        try:
            return UserQuery(
                Category(
                    int(category.get("id") or Category.ALL),
                    category.get("name") or "All",
                ),
                Period(int(years.get("id") or 0), years.get("period") or "All"),
                query.get("title") or None,
                int(item.get("count", 0)),
                item.get("last_searched_at") or datetime.now(UTC),
            )
        except (TypeError, ValueError):
            return None

    def to_dict(self) -> dict:
        """Serialize the query for MongoDB storage."""
        category = self.category or Category(Category.ALL, "All")
        years = self.years or Period(0, "All")
        return {
            "category": {"id": category.category_id, "name": category.name},
            "years": {"id": years.id, "period": years.period},
            "title": self.title or "",
        }

    def to_label(self) -> str:
        """Return a human-readable query label for menus."""
        category = self.category.name if self.category else "All"
        years = self.years.period if self.years else "All"
        title = self.title or "All"
        return f"Category: {category} | Period: {years} | Title: {title}"
