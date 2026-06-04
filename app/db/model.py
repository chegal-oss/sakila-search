from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, ClassVar


@dataclass()
class Record:
    SQL_QUERY: ClassVar[str] = ""

    @classmethod
    def get_query(cls, where_statement: str = None) -> str:
        return cls.SQL_QUERY.format(where_statement=where_statement or "")

    @classmethod
    def from_dict(cls, dict_item: dict):
        return cls(**dict_item)


@dataclass
class Film(Record):
    SQL_QUERY = """
        select f.film_id,
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
        order by f.release_year, f.rating limit %s, %s \
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
        return f"{self.title:30} {self.release_year:^26} {self.category:20} {self.rating}"



@dataclass
class Category(Record):
    POPULAR: ClassVar[int] = -1
    ALL: ClassVar[int] = 0
    SQL_QUERY = """
        select category_id, name from category 
        union select 0, 'All'
        order by category_id
    """
    category_id: int
    name: str

@dataclass
class Period(Record):
    SQL_QUERY = """
        select 
            concat(min(release_year),'-', max(release_year)) as period,
            min(release_year) as id
        from film
        group by floor((release_year - 1) / 5)
        union
        select "All", 0
        order by id;
    """
    id: int
    period: str

@dataclass
class UserQuery:
    category: Category | None = None
    years: Period | None = None
    title: str | None = None
    count: int | None = None
    last_searched_at: datetime | None = None

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> UserQuery | None:
        query = item.get("_id") or item.get("query")
        if not isinstance(query, dict):
            return None

        category = query.get("category") or {}
        years = query.get("years") or {}

        try:
            return UserQuery(
                Category(int(category.get("id") or Category.ALL), category.get("name") or "All"),
                Period(int(years.get("id") or 0), years.get("period") or "All"),
                query.get("title") or None,
                int(item.get("count", 0)),
                item.get("last_searched_at") or datetime.now(UTC),
            )
        except (TypeError, ValueError):
            return None

    def to_dict(self) -> dict:
        category = self.category or Category(Category.ALL, "All")
        years = self.years or Period(0, "All")
        return {
            "category" : {
                "id": category.category_id,
                "name": category.name
            },
            "years": {
                "id": years.id,
                "period": years.period
            },
            "title": self.title or ""
        }

    def to_label(self) -> str:
        category = self.category.name if self.category else "All"
        years = self.years.period if self.years else "All"
        title = self.title or "All"
        return f"Category: {category} | Period: {years} | Title: {title}"

