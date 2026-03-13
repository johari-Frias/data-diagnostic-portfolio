"""
test_backend.py – Unit tests for the Data Diagnostic Dashboard backend.

Covers:
    • DataProfiler.get_duplicate_count()
    • DataProfiler.get_missing_summary()
    • DataProfiler.get_type_suggestions()
    • detect_outliers_iqr()

Run with:
    pytest tests/test_backend.py -v
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.profiler import DataProfiler
from src.stats import detect_outliers_iqr


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Yield a purpose-built DataFrame that exercises every backend feature.

    Layout (8 rows):
        • Rows 0 and 1 are exact duplicates.
        • 'city' has 2 NaN values; 'score' has 1 NaN value.
        • 'score' contains a clear outlier (999) among values 1-10.
        • 'signup_date' is a string column with date-like values.
    """
    data = pd.DataFrame(
        {
            "name": [
                "Alice",
                "Alice",        # duplicate of row 0
                "Bob",
                "Charlie",
                "Diana",
                "Eve",
                "Frank",
                "Grace",
            ],
            "city": [
                "New York",
                "New York",     # duplicate of row 0
                np.nan,         # missing
                "Chicago",
                "Houston",
                np.nan,         # missing
                "Phoenix",
                "Dallas",
            ],
            "score": [
                5,
                5,              # duplicate of row 0
                7,
                3,
                8,
                6,
                999,            # obvious outlier
                np.nan,         # missing
            ],
            "signup_date": [
                "2023-01-01",
                "2023-01-01",   # duplicate of row 0
                "2023-02-14",
                "2023-03-22",
                "2023-04-10",
                "2023-05-05",
                "2023-06-18",
                "2023-07-30",
            ],
        }
    )
    return data


@pytest.fixture
def profiler(sample_dataframe: pd.DataFrame) -> DataProfiler:
    """Convenience fixture: a DataProfiler initialised with the sample data."""
    return DataProfiler(sample_dataframe)


# ──────────────────────────────────────────────────────────────────────────────
# DataProfiler — initialisation
# ──────────────────────────────────────────────────────────────────────────────

class TestDataProfilerInit:
    """Guard-rail tests for DataProfiler construction."""

    def test_rejects_non_dataframe(self) -> None:
        """Passing a non-DataFrame must raise TypeError."""
        with pytest.raises(TypeError, match="Expected a pandas DataFrame"):
            DataProfiler([1, 2, 3])

    def test_rejects_empty_dataframe(self) -> None:
        """A 0-row × 0-column DataFrame must raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            DataProfiler(pd.DataFrame())

    def test_does_not_mutate_original(self, sample_dataframe: pd.DataFrame) -> None:
        """The profiler must work on a copy, leaving the original untouched."""
        original_shape = sample_dataframe.shape
        profiler = DataProfiler(sample_dataframe)

        # Mutate the internal copy
        profiler.df.drop(profiler.df.index, inplace=True)

        assert sample_dataframe.shape == original_shape


# ──────────────────────────────────────────────────────────────────────────────
# DataProfiler.get_duplicate_count()
# ──────────────────────────────────────────────────────────────────────────────

class TestGetDuplicateCount:
    """Tests for duplicate-row detection."""

    def test_exact_duplicate_count(self, profiler: DataProfiler) -> None:
        """The fixture contains exactly 1 duplicate row (row 1 is a copy of row 0)."""
        assert profiler.get_duplicate_count() == 1

    def test_returns_int(self, profiler: DataProfiler) -> None:
        """The return value must be a plain int, not a numpy type."""
        result = profiler.get_duplicate_count()
        assert isinstance(result, int)

    def test_zero_duplicates_when_all_unique(self) -> None:
        """A DataFrame with no duplicate rows must return 0."""
        unique_df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        assert DataProfiler(unique_df).get_duplicate_count() == 0


# ──────────────────────────────────────────────────────────────────────────────
# DataProfiler.get_missing_summary()
# ──────────────────────────────────────────────────────────────────────────────

class TestGetMissingSummary:
    """Tests for the missing-value summary report."""

    def test_returns_dataframe(self, profiler: DataProfiler) -> None:
        """The result must be a DataFrame."""
        result = profiler.get_missing_summary()
        assert isinstance(result, pd.DataFrame)

    def test_columns_present(self, profiler: DataProfiler) -> None:
        """The summary must contain 'column', 'missing_count', 'missing_pct'."""
        result = profiler.get_missing_summary()
        assert set(result.columns) == {"column", "missing_count", "missing_pct"}

    def test_city_missing_count(self, profiler: DataProfiler) -> None:
        """'city' has exactly 2 NaN values in the fixture."""
        result = profiler.get_missing_summary()
        city_row = result.loc[result["column"] == "city"]
        assert int(city_row["missing_count"].iloc[0]) == 2

    def test_score_missing_count(self, profiler: DataProfiler) -> None:
        """'score' has exactly 1 NaN value in the fixture."""
        result = profiler.get_missing_summary()
        score_row = result.loc[result["column"] == "score"]
        assert int(score_row["missing_count"].iloc[0]) == 1

    def test_name_has_no_missing(self, profiler: DataProfiler) -> None:
        """'name' has zero missing values."""
        result = profiler.get_missing_summary()
        name_row = result.loc[result["column"] == "name"]
        assert int(name_row["missing_count"].iloc[0]) == 0

    def test_sorted_descending(self, profiler: DataProfiler) -> None:
        """Rows must be sorted by missing_count in descending order."""
        result = profiler.get_missing_summary()
        counts = result["missing_count"].tolist()
        assert counts == sorted(counts, reverse=True)


# ──────────────────────────────────────────────────────────────────────────────
# DataProfiler.get_type_suggestions()
# ──────────────────────────────────────────────────────────────────────────────

class TestGetTypeSuggestions:
    """Tests for the type-inference heuristic."""

    def test_returns_list(self, profiler: DataProfiler) -> None:
        """The result must be a list."""
        result = profiler.get_type_suggestions()
        assert isinstance(result, list)

    def test_date_column_flagged(self, profiler: DataProfiler) -> None:
        """The 'signup_date' column should be flagged as datetime-convertible."""
        suggestions = profiler.get_type_suggestions()
        flagged_cols = [s["column"] for s in suggestions]
        assert "signup_date" in flagged_cols

    def test_date_suggestion_dtype(self, profiler: DataProfiler) -> None:
        """The suggested dtype for 'signup_date' must be 'datetime64[ns]'."""
        suggestions = profiler.get_type_suggestions()
        date_suggestion = next(
            s for s in suggestions if s["column"] == "signup_date"
        )
        assert date_suggestion["suggested_dtype"] == "datetime64[ns]"

    def test_suggestion_has_required_keys(self, profiler: DataProfiler) -> None:
        """Each suggestion dict must contain the four required keys."""
        required = {"column", "current_dtype", "suggested_dtype", "reason"}
        for suggestion in profiler.get_type_suggestions():
            assert required.issubset(suggestion.keys())


# ──────────────────────────────────────────────────────────────────────────────
# detect_outliers_iqr()
# ──────────────────────────────────────────────────────────────────────────────

class TestDetectOutliersIQR:
    """Tests for the IQR-based outlier detector."""

    def test_detects_outlier_in_score(self, sample_dataframe: pd.DataFrame) -> None:
        """The 'score' column contains one obvious outlier (999)."""
        result = detect_outliers_iqr(sample_dataframe)
        assert result["score"] >= 1

    def test_returns_dict(self, sample_dataframe: pd.DataFrame) -> None:
        """The return type must be a plain dict."""
        result = detect_outliers_iqr(sample_dataframe)
        assert isinstance(result, dict)

    def test_all_values_are_ints(self, sample_dataframe: pd.DataFrame) -> None:
        """Every value in the returned dict must be an int."""
        result = detect_outliers_iqr(sample_dataframe)
        for count in result.values():
            assert isinstance(count, int)

    def test_only_numeric_columns_included(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Non-numeric columns ('name', 'city', 'signup_date') must be absent."""
        result = detect_outliers_iqr(sample_dataframe)
        assert "name" not in result
        assert "city" not in result
        assert "signup_date" not in result

    def test_rejects_non_dataframe(self) -> None:
        """Passing a non-DataFrame must raise TypeError."""
        with pytest.raises(TypeError, match="Expected a pandas DataFrame"):
            detect_outliers_iqr({"a": [1, 2, 3]})

    def test_rejects_no_numeric_columns(self) -> None:
        """A DataFrame with only string columns must raise ValueError."""
        str_df = pd.DataFrame({"a": ["x", "y"], "b": ["p", "q"]})
        with pytest.raises(ValueError, match="no numeric columns"):
            detect_outliers_iqr(str_df)

    def test_no_outliers_uniform_data(self) -> None:
        """A column where all values are identical should report 0 outliers."""
        uniform = pd.DataFrame({"val": [5, 5, 5, 5, 5]})
        result = detect_outliers_iqr(uniform)
        assert result["val"] == 0
