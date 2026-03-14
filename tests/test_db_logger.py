"""
test_db_logger.py – Unit tests for src.db_logger.

Uses ``unittest.mock.patch`` to mock ``psycopg2.connect`` so that
tests never touch a real database.

Run with:
    pytest tests/test_db_logger.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Helpers — set DATABASE_URL env var so db_logger can resolve it
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Inject a fake ``DATABASE_URL`` environment variable for every test."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")


# ──────────────────────────────────────────────────────────────────────────────
# Tests — log_upload()
# ──────────────────────────────────────────────────────────────────────────────


class TestLogUpload:
    """Tests for the ``log_upload`` function."""

    @patch("src.db_logger.psycopg2.connect")
    def test_successful_insert(self, mock_connect: MagicMock) -> None:
        """A successful call should execute the INSERT and return True."""
        from src.db_logger import log_upload

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        result = log_upload(
            file_name="test.csv",
            total_rows=100,
            total_columns=5,
            missing_values_count=10,
        )

        assert result is True
        mock_cursor.execute.assert_called_once()

        # Verify the parameters passed to execute()
        call_args = mock_cursor.execute.call_args
        sql, params = call_args[0]
        assert "INSERT INTO app_usage_logs" in sql
        assert params == ("test.csv", 100, 5, 10)

    @patch("src.db_logger.psycopg2.connect")
    def test_connection_failure_returns_false(self, mock_connect: MagicMock) -> None:
        """If psycopg2.connect raises, log_upload should return False gracefully."""
        import psycopg2
        from src.db_logger import log_upload

        mock_connect.side_effect = psycopg2.OperationalError("connection refused")

        result = log_upload(
            file_name="test.csv",
            total_rows=100,
            total_columns=5,
            missing_values_count=10,
        )

        assert result is False

    @patch("src.db_logger.psycopg2.connect")
    def test_execute_failure_returns_false(self, mock_connect: MagicMock) -> None:
        """If cursor.execute raises, log_upload should handle it gracefully."""
        from src.db_logger import log_upload

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("table does not exist")
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        result = log_upload(
            file_name="test.csv",
            total_rows=100,
            total_columns=5,
            missing_values_count=10,
        )

        assert result is False


# ──────────────────────────────────────────────────────────────────────────────
# Tests — get_connection()
# ──────────────────────────────────────────────────────────────────────────────


class TestGetConnection:
    """Tests for the ``get_connection`` helper."""

    @patch("src.db_logger.psycopg2.connect")
    def test_returns_connection(self, mock_connect: MagicMock) -> None:
        """Should return the connection object on success."""
        from src.db_logger import get_connection

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        conn = get_connection()

        assert conn is mock_conn
        mock_connect.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/testdb",
            sslmode="require",
        )

    def test_returns_none_when_env_var_missing(self, monkeypatch) -> None:
        """Should return None when DATABASE_URL is not in the environment."""
        from src.db_logger import get_connection

        monkeypatch.delenv("DATABASE_URL", raising=False)

        conn = get_connection()

        assert conn is None
