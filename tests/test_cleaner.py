"""
test_cleaner.py – Unit tests for src.cleaner.

Run with:
    pytest tests/test_cleaner.py -v
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.cleaner import clean_dataframe


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def dirty_dataframe() -> pd.DataFrame:
    """A DataFrame with a mix of cleaning targets.

    * ``empty_col`` — 100 % NaN (should be dropped).
    * ``score``     — numeric column with 1 missing value.
    * ``city``      — object column with 1 missing value.
    * ``name``      — no missing values.
    """
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "city": ["New York", np.nan, "Chicago", "Houston"],
            "score": [10.0, 20.0, np.nan, 40.0],
            "empty_col": [np.nan, np.nan, np.nan, np.nan],
        }
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestCleanDataframe:
    """Tests for the ``clean_dataframe`` function."""

    def test_drops_fully_empty_columns(self, dirty_dataframe: pd.DataFrame) -> None:
        """Columns that are 100 % NaN must be removed."""
        cleaned, stats = clean_dataframe(dirty_dataframe)
        assert "empty_col" not in cleaned.columns
        assert stats["columns_dropped"] == 1

    def test_fills_numeric_with_median(self, dirty_dataframe: pd.DataFrame) -> None:
        """Missing numeric values must be filled with the column median."""
        cleaned, stats = clean_dataframe(dirty_dataframe)
        # median of [10, 20, 40] == 20.0
        assert cleaned["score"].isnull().sum() == 0
        assert cleaned["score"].iloc[2] == 20.0
        assert stats["numeric_fills"] == 1

    def test_fills_categorical_with_mode(self, dirty_dataframe: pd.DataFrame) -> None:
        """Missing categorical values must be filled with the column mode."""
        cleaned, stats = clean_dataframe(dirty_dataframe)
        assert cleaned["city"].isnull().sum() == 0
        # mode can be any of the existing values; just ensure it's a string
        assert isinstance(cleaned["city"].iloc[1], str)
        assert stats["categorical_fills"] == 1

    def test_does_not_mutate_original(self, dirty_dataframe: pd.DataFrame) -> None:
        """The original DataFrame must remain untouched."""
        original_shape = dirty_dataframe.shape
        original_nulls = dirty_dataframe.isnull().sum().sum()
        clean_dataframe(dirty_dataframe)
        assert dirty_dataframe.shape == original_shape
        assert dirty_dataframe.isnull().sum().sum() == original_nulls

    def test_returns_dataframe_and_dict(self, dirty_dataframe: pd.DataFrame) -> None:
        """Return type must be a tuple of (DataFrame, dict)."""
        result = clean_dataframe(dirty_dataframe)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], pd.DataFrame)
        assert isinstance(result[1], dict)

    def test_stats_keys(self, dirty_dataframe: pd.DataFrame) -> None:
        """The stats dict must contain exactly the expected keys."""
        _, stats = clean_dataframe(dirty_dataframe)
        assert set(stats.keys()) == {
            "columns_dropped",
            "numeric_fills",
            "categorical_fills",
            "duplicates_removed",
            "outliers_capped",
        }

    def test_already_clean_data(self) -> None:
        """A DataFrame with no nulls, no dupes, and no outliers passes through."""
        # Uniform numeric values + unique strings → nothing to clean
        clean_df = pd.DataFrame({
            "a": [5] * 10,
            "b": [f"item_{i}" for i in range(10)],
        })
        cleaned, stats = clean_dataframe(clean_df)
        assert stats["columns_dropped"] == 0
        assert stats["numeric_fills"] == 0
        assert stats["categorical_fills"] == 0
        assert stats["duplicates_removed"] == 0
        assert stats["outliers_capped"] == 0

    def test_rejects_non_dataframe(self) -> None:
        """Passing a non-DataFrame must raise TypeError."""
        with pytest.raises(TypeError, match="Expected a pandas DataFrame"):
            clean_dataframe([1, 2, 3])

    # ── Duplicate removal tests ──────────────────────────────────────────

    def test_drops_exact_duplicate_rows(self) -> None:
        """Exact duplicate rows must be removed, keeping the first occurrence."""
        df = pd.DataFrame(
            {
                "name": ["Alice", "Alice", "Bob"],
                "score": [10, 10, 20],
            }
        )
        cleaned, stats = clean_dataframe(df)
        assert len(cleaned) == 2
        assert stats["duplicates_removed"] == 1
        # First occurrence is kept
        assert cleaned.iloc[0]["name"] == "Alice"
        assert cleaned.iloc[1]["name"] == "Bob"

    def test_no_duplicates_reports_zero(self) -> None:
        """When there are no duplicates, stats should report 0."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        _, stats = clean_dataframe(df)
        assert stats["duplicates_removed"] == 0

    # ── Outlier capping tests ────────────────────────────────────────────

    def test_caps_outliers_at_percentiles(self) -> None:
        """Values beyond the 1st/99th percentile must be clipped."""
        # Build a 100-row DataFrame with one extreme outlier
        values = list(range(1, 100)) + [999]
        df = pd.DataFrame({"age": values})

        cleaned, stats = clean_dataframe(df)

        assert cleaned["age"].max() <= df["age"].quantile(0.99)
        assert cleaned["age"].min() >= df["age"].quantile(0.01)
        assert stats["outliers_capped"] >= 1

    def test_no_outliers_uniform_data(self) -> None:
        """Uniform data has no outliers — nothing should be capped."""
        df = pd.DataFrame({"val": [5, 5, 5, 5, 5]})
        _, stats = clean_dataframe(df)
        assert stats["outliers_capped"] == 0

    def test_caps_do_not_mutate_original(self) -> None:
        """Outlier capping must not alter the original DataFrame."""
        values = list(range(1, 100)) + [999]
        df = pd.DataFrame({"age": values})
        original_max = df["age"].max()

        clean_dataframe(df)

        assert df["age"].max() == original_max

