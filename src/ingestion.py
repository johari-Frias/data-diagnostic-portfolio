"""
ingestion.py – Data-ingestion back-end for the Data Diagnostic Dashboard.

Provides a single public function, `load_data()`, that accepts a Streamlit
UploadedFile object and returns either a Pandas DataFrame on success or a
descriptive error string on failure.

Supported formats: .csv, .xlsx
"""

from __future__ import annotations

import os
from typing import Union

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def _get_extension(filename: str) -> str:
    """Return the lowercased file extension (e.g. '.csv')."""
    return os.path.splitext(filename)[-1].lower()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading data …")
def load_data(uploaded_file) -> Union[pd.DataFrame, str]:
    """Read a user-uploaded file into a Pandas DataFrame.

    Parameters
    ----------
    uploaded_file : streamlit.runtime.uploaded_file_manager.UploadedFile
        The file object returned by ``st.file_uploader()``.

    Returns
    -------
    pd.DataFrame
        The parsed data, if ingestion succeeds.
    str
        A human-readable error message, if ingestion fails.

    Notes
    -----
    * The function is decorated with ``@st.cache_data`` so the file is only
      parsed once per unique upload; subsequent re-renders reuse the cached
      result.
    * Only ``.csv`` and ``.xlsx`` extensions are accepted.  Any other
      extension returns an error string immediately.
    * Common failure modes (empty file, encoding errors, corrupt Excel
      workbooks) are caught and surfaced as clear messages rather than raw
      tracebacks.
    """

    # --- Guard: no file provided -------------------------------------------
    if uploaded_file is None:
        return "⚠️ No file was uploaded. Please upload a .csv or .xlsx file."

    filename: str = uploaded_file.name
    ext: str = _get_extension(filename)

    # --- Guard: unsupported extension --------------------------------------
    if ext not in _SUPPORTED_EXTENSIONS:
        return (
            f"❌ Unsupported file type '{ext}'. "
            f"Please upload one of: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}."
        )

    # --- Guard: empty / zero-byte file -------------------------------------
    uploaded_file.seek(0, 2)          # move cursor to the end
    file_size = uploaded_file.tell()  # current position == total bytes
    uploaded_file.seek(0)             # reset cursor for readers

    if file_size == 0:
        return f"⚠️ The uploaded file '{filename}' is empty (0 bytes)."

    # --- Read the file into a DataFrame ------------------------------------
    try:
        if ext == ".csv":
            df = _read_csv(uploaded_file)
        else:  # .xlsx
            df = _read_excel(uploaded_file)

    except pd.errors.EmptyDataError:
        return (
            f"⚠️ The file '{filename}' contains no parseable data. "
            "Please check that it is not blank or header-only."
        )
    except UnicodeDecodeError as exc:
        return (
            f"❌ Encoding error while reading '{filename}': {exc}. "
            "Try re-saving the file as UTF-8."
        )
    except ValueError as exc:
        return f"❌ Value error while reading '{filename}': {exc}"
    except Exception as exc:  # noqa: BLE001 – catch-all for unexpected issues
        return f"❌ Failed to read '{filename}': {type(exc).__name__} – {exc}"

    # --- Post-read validation ----------------------------------------------
    if df.empty:
        return (
            f"⚠️ The file '{filename}' was read successfully but produced an "
            "empty DataFrame (0 rows × 0 columns). Verify the file contents."
        )

    return df


# ---------------------------------------------------------------------------
# Internal readers
# ---------------------------------------------------------------------------

def _read_csv(uploaded_file) -> pd.DataFrame:
    """Attempt to read a CSV, falling back through common encodings."""
    encodings = ["utf-8", "latin-1", "cp1252"]
    last_error: Exception | None = None

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding=enc)
        except (UnicodeDecodeError, UnicodeError) as exc:
            last_error = exc
            continue

    # If none of the encodings worked, raise the last error encountered.
    raise last_error  # type: ignore[misc]


def _read_excel(uploaded_file) -> pd.DataFrame:
    """Read an Excel (.xlsx) workbook."""
    uploaded_file.seek(0)
    return pd.read_excel(uploaded_file, engine="openpyxl")
