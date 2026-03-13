# 🩺 Data Diagnostic Dashboard

**Instantly profile, diagnose, and visualise data-quality issues in any CSV or Excel file — no code required.**

Upload a dataset and get an automated health report covering missing values, duplicate rows, dtype mismatches, and statistical outliers, all rendered as interactive Plotly charts inside a sleek Streamlit interface.

---

## 📌 The Problem

> Data analysts spend up to **60 % of their time** cleaning and profiling messy spreadsheets before any real analysis can begin. Manual inspection doesn't scale, and errors slip through when the dataset grows past a few thousand rows.

## 💡 The Solution

The **Data Diagnostic Dashboard** automates the entire profiling phase. Drop in a `.csv` or `.xlsx` file and the app instantly surfaces:

- How many rows and columns you're working with.
- Exactly which columns contain missing values — and what percentage is null.
- How many exact duplicate rows exist.
- Which string columns secretly hold dates, booleans, or numbers that should be re-typed.
- Which numeric columns contain statistical outliers (IQR method) — with an interactive box plot to confirm.

---

## ✨ Features

| Feature | Description |
|---|---|
| **📂 Smart Ingestion** | Handles `.csv` (with automatic encoding fallback) and `.xlsx` files. Cached via `@st.cache_data`. |
| **🧬 Missing Value Profiling** | Per-column null count and percentage, sorted by severity. |
| **🔁 Duplicate Detection** | Exact duplicate-row count surfaced as a top-level KPI. |
| **🔮 Automated Type Inference** | Detects date-like strings, boolean-like values, numeric strings, and low-cardinality categoricals — then suggests optimal Pandas dtypes. |
| **📈 IQR Outlier Detection** | Flags values outside the 1.5 × IQR fence for every numeric column. |
| **📊 Interactive Plotly Visuals** | Select any numeric column and render a live box plot to visually confirm outliers. |

---

## 🏗️ Architecture & Tech Stack

```
DataAppProject/
├── app.py               ← Streamlit UI (frontend view layer)
├── requirements.txt
├── .gitignore
├── src/                  ← Backend logic (strictly decoupled from UI)
│   ├── ingestion.py      ·  File upload, parsing, caching
│   ├── profiler.py       ·  DataProfiler class (missing vals, dupes, types)
│   └── stats.py          ·  IQR outlier detection
└── tests/
    └── test_backend.py   ← 23 pytest unit tests
```

**Design principle:** The `src/` backend is **100 % UI-agnostic** — every function and class returns plain Python data structures (DataFrames, dicts, ints). The `app.py` frontend simply consumes these outputs and renders them. This separation makes the backend independently testable and reusable outside Streamlit.

| Layer | Technology |
|---|---|
| **Language** | Python 3.12 |
| **Frontend** | Streamlit |
| **Visualisation** | Plotly Express |
| **Data Processing** | Pandas, NumPy |
| **Testing** | Pytest |

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/DataAppProject.git
cd DataAppProject

# 2. Create & activate a virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run app.py
```

The app will open automatically at **http://localhost:8501**. Upload any `.csv` or `.xlsx` file via the sidebar to begin.

---

## 🧪 Testing

The project includes a comprehensive test suite covering both `DataProfiler` and `detect_outliers_iqr`.

```bash
# Run the full suite
python -m pytest tests/test_backend.py -v
```

```
============================= 23 passed in 2.32s ==============================
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
