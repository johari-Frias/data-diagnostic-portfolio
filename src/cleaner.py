"""
cleaner.py – Automated data-cleaning engine for the Data Diagnostic Dashboard.

Provides a single public function, ``clean_dataframe()``, that applies a set
of safe, deterministic cleaning steps to a Pandas DataFrame and returns both
the cleaned result and a summary of what was changed.

This module has **zero** UI-framework dependencies.
"""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Apply automated cleaning to a DataFrame.

    Cleaning steps (in order):
        1. **Drop fully-empty columns** — any column where every value is null.
        2. **Fill numeric nulls** — replace ``NaN`` in numeric columns with
           the column median.
        3. **Fill categorical nulls** — replace ``NaN`` in object / category
           columns with the column mode (most frequent value).
        4. **Drop duplicates** — remove exact duplicate rows, keeping the
           first occurrence.
        5. **Cap outliers** — for every numeric column, clip values below the
           1st percentile or above the 99th percentile to those bounds.

    Parameters
    ----------
    df : pd.DataFrame
        The raw DataFrame to clean.  This is **not** modified; a copy is
        used internally.

    Returns
    -------
    tuple[pd.DataFrame, dict[str, int]]
        A two-element tuple:

        * **cleaned_df** — the cleaned DataFrame.
        * **stats** — a dictionary summarising what was done::

              {
                  "columns_dropped": 2,
                  "numeric_fills": 54,
                  "categorical_fills": 12,
                  "duplicates_removed": 3,
                  "outliers_capped": 7,
              }

    Raises
    ------
    TypeError
        If *df* is not a ``pandas.DataFrame``.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected a pandas DataFrame, got {type(df).__name__}."
        )

    cleaned = df.copy()
    stats: Dict[str, int] = {
        "columns_dropped": 0,
        "numeric_fills": 0,
        "categorical_fills": 0,
        "duplicates_removed": 0,
        "outliers_capped": 0,
    }

    # ── Step 1: Drop columns that are 100 % empty ─────────────────────────
    all_null_cols = [
        col for col in cleaned.columns if cleaned[col].isnull().all()
    ]
    if all_null_cols:
        cleaned.drop(columns=all_null_cols, inplace=True)
        stats["columns_dropped"] = len(all_null_cols)

    # ── Step 2: Fill missing numeric values with column median ────────────
    numeric_cols = cleaned.select_dtypes(include="number").columns
    for col in numeric_cols:
        n_missing = int(cleaned[col].isnull().sum())
        if n_missing > 0:
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())
            stats["numeric_fills"] += n_missing

    # ── Step 3: Fill missing categorical values with column mode ──────────
    categorical_cols = cleaned.select_dtypes(
        include=["object", "category"]
    ).columns
    for col in categorical_cols:
        n_missing = int(cleaned[col].isnull().sum())
        if n_missing > 0:
            mode_values = cleaned[col].mode()
            if not mode_values.empty:
                cleaned[col] = cleaned[col].fillna(mode_values.iloc[0])
                stats["categorical_fills"] += n_missing

    # ── Step 4: Drop exact duplicate rows ─────────────────────────────────
    n_before = len(cleaned)
    cleaned = cleaned.drop_duplicates(keep="first")
    stats["duplicates_removed"] = n_before - len(cleaned)

    # ── Step 5: Cap outliers at 1st / 99th percentile ─────────────────────
    numeric_cols = cleaned.select_dtypes(include="number").columns
    for col in numeric_cols:
        p01 = cleaned[col].quantile(0.01)
        p99 = cleaned[col].quantile(0.99)
        outlier_mask = (cleaned[col] < p01) | (cleaned[col] > p99)
        n_outliers = int(outlier_mask.sum())
        if n_outliers > 0:
            cleaned[col] = cleaned[col].clip(lower=p01, upper=p99)
            stats["outliers_capped"] += n_outliers

    return cleaned, stats
