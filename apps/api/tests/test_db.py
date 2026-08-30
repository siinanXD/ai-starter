from app.core.db import _connect_args


def test_postgres_connect_args_include_timeout() -> None:
    assert _connect_args("postgresql+psycopg://starter:starter@localhost:5432/starter") == {
        "connect_timeout": 5
    }


def test_sqlite_connect_args_stay_local() -> None:
    assert _connect_args("sqlite://") == {"check_same_thread": False}
