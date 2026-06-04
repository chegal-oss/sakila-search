from app.db.repository import SakilaRepo


class FakeConnector:
    """Connector test double that records executed queries."""

    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        return self.rows


def test_get_films_uses_bound_parameters_for_filters():
    connector = FakeConnector()
    repo = SakilaRepo(connector)

    list(repo.get_films(category_id=3, years="2001-2005", search_title="Cat"))

    query, params = connector.calls[0]
    assert "c.category_id = ?" in query
    assert "f.release_year between ? and ?" in query
    assert "lower(f.title) like ?" in query
    assert params == (3, 2001, 2005, "%cat%", 10, 0)
