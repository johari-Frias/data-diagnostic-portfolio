"""
stats.py – Statistical analysis utilities for the Data Diagnostic Dashboard.

Provides standalone functions for outlier detection and related
descriptive-statistics helpers.  This module has **no** UI-framework
dependencies; every public function accepts a Pandas DataFrame and
returns plain Python data structures.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_outliers_iqr(df: pd.DataFrame) -> Dict[str, int]:
    """Detect outliers in every numeric column using the IQR method.

    The Interquartile Range (IQR) is defined as ``Q3 − Q1``.  A value is
    classified as an outlier if it falls **below** ``Q1 − 1.5 × IQR`` or
    **above** ``Q3 + 1.5 × IQR``.

    Only columns with a numeric dtype (``int``, ``float``, or their
    nullable variants) are evaluated; all other columns are silently
    skipped.

    Args:
        df: The DataFrame to analyse.  The original data is **never**
            modified.

    Returns:
        A dictionary mapping each numeric column name (``str``) to the
        integer count of outlier values found in that column.  Columns
        with zero outliers are still included so the caller has a
        complete picture.

    Raises:
        TypeError: If *df* is not a ``pandas.DataFrame``.
        ValueError: If *df* contains no numeric columns at all.

    Example::

        >>> import pandas as pd
        >>> data = pd.DataFrame({
        ...     "age":    [25, 30, 28, 200, 35, 29],
        ...     "salary": [50_000, 55_000, 52_000, 300_000, 48_000, 51_000],
        ...     "name":   ["A", "B", "C", "D", "E", "F"],
        ... })
        >>> detect_outliers_iqr(data)
        {'age': 1, 'salary': 1}
    """
    # --- Input validation --------------------------------------------------
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected a pandas DataFrame, got {type(df).__name__}."
        )

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        raise ValueError(
            "The DataFrame contains no numeric columns to evaluate."
        )

    # --- IQR computation per column ----------------------------------------
    outlier_counts: Dict[str, int] = {}

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()

        if series.empty:
            outlier_counts[col] = 0
            continue

        q1: float = float(series.quantile(0.25))
        q3: float = float(series.quantile(0.75))
        iqr: float = q3 - q1

        lower_bound: float = q1 - 1.5 * iqr
        upper_bound: float = q3 + 1.5 * iqr

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_counts[col] = int(outlier_mask.sum())

    return outlier_counts
