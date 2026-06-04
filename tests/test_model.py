from app.db.model import Period


def test_periods_are_built_from_release_years():
    periods = Period.from_release_years(
        [
            {"release_year": 1990},
            {"release_year": 1991},
            {"release_year": 1995},
            {"release_year": 2001},
        ]
    )

    assert periods == [
        Period(0, "All"),
        Period(1990, "1990-1990"),
        Period(1991, "1991-1995"),
        Period(2001, "2001-2001"),
    ]
