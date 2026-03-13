"""
profiler.py – Standalone data-profiling engine for the Data Diagnostic Dashboard.

Provides the ``DataProfiler`` class, which accepts a Pandas DataFrame and
exposes methods for missing-value analysis, duplicate detection, and
data-type inference/suggestions.

This module has **zero** UI-framework dependencies; all public methods
return plain Python data structures (dicts, DataFrames, ints) so any
frontend can consume the results without coupling.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Union

import pandas as pd


# ---------------------------------------------------------------------------
# Compiled patterns used by the type-suggestion heuristics
# ---------------------------------------------------------------------------

# Matches common date-like strings: YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY,
# DD/MM/YYYY, and variants with time components.
_DATE_PATTERN = re.compile(
    r"^\d{2,4}[\-/\.]\d{1,2}[\-/\.]\d{1,4}"  # date part
    r"(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?$"      # optional time part
)

# Matches integers (possibly negative) with no decimal component.
_INT_PATTERN = re.compile(r"^-?\d+$")

# Matches numbers with a decimal point (float-like).
_FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+$")

# Matches common boolean-like strings.
_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}


class DataProfiler:
    """A UI-agnostic profiler that diagnoses common data-quality issues.

    Attributes:
        df: A *copy* of the DataFrame provided at construction time.
            The original is never mutated.

    Example::

        profiler = DataProfiler(my_dataframe)
        missing  = profiler.get_missing_summary()
        dupes    = profiler.get_duplicate_count()
        types    = profiler.get_type_suggestions()
    """

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def __init__(self, df: pd.DataFrame) -> None:
        """Initialise the profiler with a Pandas DataFrame.

        Args:
            df: The DataFrame to profile.  A shallow copy is stored
                internally so the caller's data is never modified.

        Raises:
            TypeError: If *df* is not a ``pandas.DataFrame``.
            ValueError: If *df* is completely empty (0 rows **and**
                0 columns).
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"Expected a pandas DataFrame, got {type(df).__name__}."
            )
        if df.empty and len(df.columns) == 0:
            raise ValueError(
                "The provided DataFrame is empty (0 rows × 0 columns)."
            )

        self.df: pd.DataFrame = df.copy()

    # ------------------------------------------------------------------ #
    # Missing-value analysis
    # ------------------------------------------------------------------ #

    def get_missing_summary(self) -> pd.DataFrame:
        """Return a per-column summary of missing (null) values.

        Returns:
            A ``pd.DataFrame`` with three columns:

            * **column** – the original column name.
            * **missing_count** – absolute number of null entries.
            * **missing_pct** – the percentage of the column that is null,
              rounded to two decimal places.

            Rows are sorted in descending order of *missing_count*.
            Columns with zero missing values are still included so the
            caller has a complete picture.

        Example::

            >>> profiler.get_missing_summary()
               column  missing_count  missing_pct
            0   city             12        24.00
            1   age               3         6.00
            2   name              0         0.00
        """
        total_rows = len(self.df)
        missing_count = self.df.isnull().sum()
        missing_pct = (
            (missing_count / total_rows * 100).round(2)
            if total_rows > 0
            else missing_count * 0.0
        )

        summary = pd.DataFrame({
            "column": missing_count.index,
            "missing_count": missing_count.values,
            "missing_pct": missing_pct.values,
        })

        return (
            summary
            .sort_values("missing_count", ascending=False)
            .reset_index(drop=True)
        )

    # ------------------------------------------------------------------ #
    # Duplicate detection
    # ------------------------------------------------------------------ #

    def get_duplicate_count(self) -> int:
        """Return the total number of exact duplicate rows.

        A row is counted as a duplicate if **all** of its column values
        are identical to at least one other row.  The *first* occurrence
        is kept; only subsequent copies are counted.

        Returns:
            An integer representing the number of duplicate rows.

        Example::

            >>> profiler.get_duplicate_count()
            7
        """
        return int(self.df.duplicated().sum())

    # ------------------------------------------------------------------ #
    # Data-type inference & suggestions
    # ------------------------------------------------------------------ #

    def get_type_suggestions(
        self,
        sample_size: int = 200,
        threshold: float = 0.80,
    ) -> List[Dict[str, str]]:
        """Compare current dtypes against heuristically optimal types.

        The method samples non-null values from every ``object``-typed
        column and checks whether the majority resemble dates, integers,
        floats, or booleans.  Columns that already carry an appropriate
        Pandas dtype are skipped.

        Args:
            sample_size: Maximum number of non-null values to inspect per
                column.  Larger values improve accuracy at the cost of
                speed.  Defaults to ``200``.
            threshold: Fraction (0 – 1) of sampled values that must match
                a pattern before a suggestion is emitted.  Defaults to
                ``0.80`` (80 %).

        Returns:
            A list of dictionaries, one per actionable suggestion.  Each
            dict contains:

            * **column** – the column name.
            * **current_dtype** – the column's existing Pandas dtype
              (as a string).
            * **suggested_dtype** – the recommended Pandas dtype string.
            * **reason** – a short, human-readable explanation.

            If there are no suggestions the list is empty.

        Example::

            >>> profiler.get_type_suggestions()
            [
                {
                    "column": "order_date",
                    "current_dtype": "object",
                    "suggested_dtype": "datetime64[ns]",
                    "reason": "93% of sampled values resemble date strings "
                              "(e.g. '2024-01-15')."
                },
            ]
        """
        suggestions: List[Dict[str, str]] = []

        for col in self.df.columns:
            current_dtype = str(self.df[col].dtype)

            # Only inspect object (string) columns – numeric / datetime
            # columns are already typed correctly by Pandas.
            if current_dtype != "object":
                continue

            sample = (
                self.df[col]
                .dropna()
                .astype(str)
                .str.strip()
            )

            if sample.empty:
                continue

            if len(sample) > sample_size:
                sample = sample.sample(n=sample_size, random_state=42)

            n_sampled = len(sample)

            # --- Check for date-like values --------------------------------
            date_matches = sample.apply(lambda v: bool(_DATE_PATTERN.match(v)))
            date_ratio = date_matches.sum() / n_sampled

            if date_ratio >= threshold:
                example = sample[date_matches].iloc[0]
                suggestions.append({
                    "column": col,
                    "current_dtype": current_dtype,
                    "suggested_dtype": "datetime64[ns]",
                    "reason": (
                        f"{date_ratio:.0%} of sampled values resemble date "
                        f"strings (e.g. '{example}')."
                    ),
                })
                continue  # one suggestion per column

            # --- Check for boolean-like values -----------------------------
            bool_matches = sample.str.lower().isin(_BOOL_VALUES)
            bool_ratio = bool_matches.sum() / n_sampled

            if bool_ratio >= threshold:
                suggestions.append({
                    "column": col,
                    "current_dtype": current_dtype,
                    "suggested_dtype": "bool",
                    "reason": (
                        f"{bool_ratio:.0%} of sampled values are "
                        f"boolean-like (true/false, yes/no, 0/1)."
                    ),
                })
                continue

            # --- Check for integer-like values -----------------------------
            int_matches = sample.apply(lambda v: bool(_INT_PATTERN.match(v)))
            int_ratio = int_matches.sum() / n_sampled

            if int_ratio >= threshold:
                suggestions.append({
                    "column": col,
                    "current_dtype": current_dtype,
                    "suggested_dtype": "Int64",
                    "reason": (
                        f"{int_ratio:.0%} of sampled values are "
                        f"integer-like strings."
                    ),
                })
                continue

            # --- Check for float-like values -------------------------------
            float_matches = sample.apply(
                lambda v: bool(_FLOAT_PATTERN.match(v))
            )
            float_ratio = (float_matches.sum() + int_matches.sum()) / n_sampled

            if float_ratio >= threshold:
                suggestions.append({
                    "column": col,
                    "current_dtype": current_dtype,
                    "suggested_dtype": "float64",
                    "reason": (
                        f"{float_ratio:.0%} of sampled values are "
                        f"numeric strings."
                    ),
                })
                continue

            # --- Check cardinality for categorical suggestion --------------
            suggestion = self._check_categorical(col, current_dtype)
            if suggestion is not None:
                suggestions.append(suggestion)

        return suggestions

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _check_categorical(
        self,
        col: str,
        current_dtype: str,
        cardinality_ratio: float = 0.05,
    ) -> Optional[Dict[str, str]]:
        """Suggest ``category`` dtype when cardinality is very low.

        Args:
            col: Column name.
            current_dtype: The column's current dtype string.
            cardinality_ratio: If the number of unique values divided by
                the total row count is below this threshold, a
                ``category`` suggestion is returned.

        Returns:
            A suggestion dict, or ``None`` if the column does not
            qualify.
        """
        n_rows = len(self.df)
        if n_rows == 0:
            return None

        n_unique = self.df[col].nunique()
        ratio = n_unique / n_rows

        if ratio <= cardinality_ratio and n_unique >= 2:
            return {
                "column": col,
                "current_dtype": current_dtype,
                "suggested_dtype": "category",
                "reason": (
                    f"Only {n_unique} unique values in {n_rows:,} rows "
                    f"({ratio:.1%} cardinality). Converting to 'category' "
                    f"may reduce memory usage."
                ),
            }
        return None
