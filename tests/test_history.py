from app.db.history import SQLiteHistoryConnector
from app.db.model import Category, Period, UserQuery


def test_sqlite_history_saves_and_groups_popular_queries(tmp_path):
    with SQLiteHistoryConnector(tmp_path / "history.sqlite") as history:
        query = UserQuery(Category(1, "Action"), Period(2001, "2001-2005"), "cat")
        history.save_query(query)
        history.save_query(query)
        history.save_query(UserQuery(Category(2, "Animation"), Period(0, "All"), None))

        popular = history.get_popular_queries(5)

    assert [item.to_label() for item in popular] == [
        "Category: Action | Period: 2001-2005 | Title: cat",
        "Category: Animation | Period: All | Title: All",
    ]
    assert [item.count for item in popular] == [2, 1]
