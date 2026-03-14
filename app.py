"""
app.py – Main entry point for the Data Diagnostic Dashboard.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.cleaner import clean_dataframe
from src.db_logger import log_upload
from src.ingestion import load_data
from src.profiler import DataProfiler
from src.stats import detect_outliers_iqr

# ──────────────────────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Data Diagnostic Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS for a polished, premium look
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ── Google Font ─────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── KPI metric cards ────────────────────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2f 0%, #2b2b40 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetric"] label {
        color: #a0a0b8 !important;
        font-weight: 500;
        letter-spacing: 0.4px;
        text-transform: uppercase;
        font-size: 0.72rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700;
        font-size: 2rem !important;
    }

    /* ── Section headers ─────────────────────────────────────────────────── */
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #c4c4e0;
        border-left: 4px solid #6c63ff;
        padding-left: 12px;
        margin-bottom: 8px;
    }

    /* ── Sidebar branding ─────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16162a 0%, #1c1c34 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h1 {
        color: #6c63ff;
    }

    /* ── File uploader styling ───────────────────────────────────────── */
    div[data-testid="stFileUploader"] label p {
        font-weight: 600;
        color: #d0d0e8;
    }

    /* ── Divider ─────────────────────────────────────────────────────── */
    .soft-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin: 28px 0 20px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar – branding & file upload
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🩺 Data Diagnostic")
    st.caption("Upload a dataset to get an instant health check.")

    st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=["csv", "xlsx"],
        help="Supported formats: .csv and .xlsx",
    )

    st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#555; font-size:0.75rem; text-align:center;'>"
        "Built with Streamlit · Plotly · Pandas</p>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Main content area
# ──────────────────────────────────────────────────────────────────────────────

if uploaded_file is None:
    # ── Landing / empty state ─────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding:80px 20px 40px;">
            <h1 style="font-size:2.6rem; font-weight:700;
                        background: linear-gradient(90deg, #6c63ff, #48cfad);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;">
                Data Diagnostic Dashboard
            </h1>
            <p style="color:#888; font-size:1.05rem; max-width:520px;
                       margin:12px auto 0;">
                Upload a <strong>.csv</strong> or <strong>.xlsx</strong> file
                in the sidebar to instantly profile your data — missing values,
                duplicates, type mismatches, and outliers — all in one view.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ── Ingest the file ───────────────────────────────────────────────────────
result = load_data(uploaded_file)

if isinstance(result, str):
    st.error(result)
    st.stop()

df: pd.DataFrame = result

# ── Initialise backend engines ────────────────────────────────────────────
profiler = DataProfiler(df)
duplicate_count: int = profiler.get_duplicate_count()
missing_summary: pd.DataFrame = profiler.get_missing_summary()
type_suggestions: list = profiler.get_type_suggestions()

# ── Log this upload to the cloud database ─────────────────────────────────
log_upload(
    file_name=uploaded_file.name,
    total_rows=len(df),
    total_columns=len(df.columns),
    missing_values_count=int(missing_summary["missing_count"].sum()),
)

# ──────────────────────────────────────────────────────────────────────────────
# TOP BAND — high-level KPIs
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    "<p style='color:#6c63ff; font-weight:700; font-size:1.5rem; "
    "margin-bottom:4px;'>📊 Dataset Overview</p>",
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(label="Total Rows", value=f"{len(df):,}")
with kpi2:
    st.metric(label="Total Columns", value=f"{len(df.columns):,}")
with kpi3:
    st.metric(
        label="Duplicate Rows",
        value=f"{duplicate_count:,}",
        delta=f"{duplicate_count / len(df) * 100:.1f}% of rows" if len(df) > 0 else "0%",
        delta_color="inverse",
    )

st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# BODY — Data Health
# ──────────────────────────────────────────────────────────────────────────────

st.markdown('<p class="section-header">🧬 Data Health</p>', unsafe_allow_html=True)

health_tab1, health_tab2, health_tab3 = st.tabs(
    ["Missing Values", "Type Suggestions", "Data Preview"]
)

# ── Tab 1: Missing Values ────────────────────────────────────────────────
with health_tab1:
    if missing_summary["missing_count"].sum() == 0:
        st.success("✅ No missing values detected — your dataset is complete!")
    else:
        total_missing = int(missing_summary["missing_count"].sum())
        total_cells = len(df) * len(df.columns)
        st.info(
            f"Found **{total_missing:,}** missing values across "
            f"**{(missing_summary['missing_count'] > 0).sum()}** columns "
            f"({total_missing / total_cells * 100:.2f}% of all cells)."
        )

    st.dataframe(
        missing_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "column": st.column_config.TextColumn("Column"),
            "missing_count": st.column_config.NumberColumn(
                "Missing Count", format="%d"
            ),
            "missing_pct": st.column_config.ProgressColumn(
                "Missing %", min_value=0, max_value=100, format="%.1f%%"
            ),
        },
    )

# ── Tab 2: Type Suggestions ─────────────────────────────────────────────
with health_tab2:
    if type_suggestions:
        st.warning(
            f"🔎 **{len(type_suggestions)}** column(s) may benefit from a "
            "dtype conversion."
        )
        st.dataframe(
            pd.DataFrame(type_suggestions),
            use_container_width=True,
            hide_index=True,
            column_config={
                "column": st.column_config.TextColumn("Column"),
                "current_dtype": st.column_config.TextColumn("Current Type"),
                "suggested_dtype": st.column_config.TextColumn("Suggested Type"),
                "reason": st.column_config.TextColumn("Reason"),
            },
        )
    else:
        st.success(
            "✅ All column dtypes look optimal — no suggestions at this time."
        )

# ── Tab 3: Data Preview ─────────────────────────────────────────────────
with health_tab3:
    st.dataframe(df, use_container_width=True, height=400)

st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# BODY — Data Explorer & Anomaly Detector
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("### 📊 Data Explorer & Anomaly Detector")

eda_col1, eda_col2 = st.columns(2)

# ── Feature A: Column Dropper ─────────────────────────────────────────────
with eda_col1:
    st.markdown(
        '<p class="section-header">🗑️ Column Dropper</p>',
        unsafe_allow_html=True,
    )
    st.caption("Select columns you want to permanently remove before cleaning.")
    columns_to_drop = st.multiselect(
        "Columns to drop",
        options=list(df.columns),
        default=[],
        help="These columns will be removed when you click the Clean button.",
    )

# ── Feature B: Anomaly Visualizer ─────────────────────────────────────────
with eda_col2:
    st.markdown(
        '<p class="section-header">🔴 Anomaly Visualizer</p>',
        unsafe_allow_html=True,
    )
    st.caption("Pick a numeric column to see outliers highlighted in red.")

    eda_numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if eda_numeric_cols:
        import altair as alt

        eda_selected = st.selectbox(
            "Select a numeric column",
            options=eda_numeric_cols,
            index=0,
            key="eda_anomaly_select",
            help="Values below the 1st or above the 99th percentile are flagged.",
        )

        if eda_selected:
            col_series = df[eda_selected].dropna().reset_index(drop=True)
            p01 = col_series.quantile(0.01)
            p99 = col_series.quantile(0.99)

            chart_df = pd.DataFrame({
                "Row Index": range(len(col_series)),
                eda_selected: col_series.values,
                "Status": [
                    "Outlier" if v < p01 or v > p99 else "Normal"
                    for v in col_series.values
                ],
            })

            color_scale = alt.Scale(
                domain=["Normal", "Outlier"],
                range=["#6c63ff", "#ff4d4f"],
            )

            scatter = (
                alt.Chart(chart_df)
                .mark_circle(size=50, opacity=0.8)
                .encode(
                    x=alt.X("Row Index:Q"),
                    y=alt.Y(f"{eda_selected}:Q"),
                    color=alt.Color(
                        "Status:N",
                        scale=color_scale,
                        legend=alt.Legend(title="Point Status"),
                    ),
                    tooltip=["Row Index", eda_selected, "Status"],
                )
                .properties(height=320)
                .configure_view(strokeWidth=0)
                .configure(
                    background="rgba(0,0,0,0)",
                    axis=alt.AxisConfig(
                        gridColor="rgba(255,255,255,0.05)",
                        labelColor="#a0a0b8",
                        titleColor="#c4c4e0",
                    ),
                    legend=alt.LegendConfig(
                        labelColor="#a0a0b8",
                        titleColor="#c4c4e0",
                    ),
                )
                .interactive()
            )

            st.altair_chart(scatter, use_container_width=True)

            n_outliers_vis = (chart_df["Status"] == "Outlier").sum()
            st.caption(
                f"**{n_outliers_vis}** outlier(s) detected "
                f"(below P1 = {p01:,.2f} or above P99 = {p99:,.2f})."
            )
    else:
        st.info("ℹ️ No numeric columns available for anomaly visualisation.")

st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# BODY — Automated Data Cleaning
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<p class="section-header">🧹 Automated Data Cleaning</p>',
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#888; font-size:0.9rem; margin-bottom:16px;'>"
    "Drop 100% empty columns · fill numeric nulls with the median · "
    "fill text nulls with the mode · remove duplicate rows · "
    "cap outliers at the 1st/99th percentile."
    "</p>",
    unsafe_allow_html=True,
)

if st.button("🧼 Clean & Download Data", type="primary", use_container_width=True):
    cleaned_df, clean_stats = clean_dataframe(df, columns_to_drop=columns_to_drop)

    # ── Summary of actions ────────────────────────────────────────────────
    act1, act2, act3, act4, act5 = st.columns(5)
    act1.metric("Columns Dropped", clean_stats["columns_dropped"])
    act2.metric("Numeric Fills", clean_stats["numeric_fills"])
    act3.metric("Categorical Fills", clean_stats["categorical_fills"])
    act4.metric("Duplicates Removed", clean_stats["duplicates_removed"])
    act5.metric("Outliers Capped", clean_stats["outliers_capped"])

    st.success(
        f"✅ Cleaning complete — the result has "
        f"**{len(cleaned_df):,}** rows × **{len(cleaned_df.columns):,}** columns."
    )

    # ── Offer CSV download ────────────────────────────────────────────────
    csv_bytes = cleaned_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download cleaned_data.csv",
        data=csv_bytes,
        file_name="cleaned_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# BODY — Outlier Diagnostics
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<p class="section-header">📈 Outlier Diagnostics</p>',
    unsafe_allow_html=True,
)

numeric_cols = df.select_dtypes(include="number").columns.tolist()

if not numeric_cols:
    st.info("ℹ️ No numeric columns found — outlier analysis is not applicable.")
    st.stop()

# Run the IQR detector
outlier_counts = detect_outliers_iqr(df)

# ── Outlier summary cards ────────────────────────────────────────────────
outlier_df = pd.DataFrame(
    [
        {"Column": col, "Outlier Count": count}
        for col, count in outlier_counts.items()
    ]
).sort_values("Outlier Count", ascending=False).reset_index(drop=True)

total_outliers = outlier_df["Outlier Count"].sum()

col_summary, col_table = st.columns([1, 2])

with col_summary:
    st.metric(
        label="Total Outlier Values",
        value=f"{total_outliers:,}",
    )
    if total_outliers == 0:
        st.success("No outliers detected across any numeric column.")
    else:
        flagged = (outlier_df["Outlier Count"] > 0).sum()
        st.warning(
            f"**{flagged}** of **{len(numeric_cols)}** numeric columns "
            "contain at least one outlier."
        )

with col_table:
    st.dataframe(
        outlier_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Column": st.column_config.TextColumn("Column"),
            "Outlier Count": st.column_config.NumberColumn(
                "Outlier Count", format="%d"
            ),
        },
    )

st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Visualization — Interactive box plot
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<p class="section-header">🔍 Visual Outlier Inspector</p>',
    unsafe_allow_html=True,
)

selected_col = st.selectbox(
    "Select a numeric column to inspect",
    options=numeric_cols,
    index=0,
    help="Choose any numeric column to render a Plotly box plot.",
)

if selected_col:
    fig = px.box(
        df,
        y=selected_col,
        points="outliers",
        title=f"Box Plot — {selected_col}",
        template="plotly_dark",
        color_discrete_sequence=["#6c63ff"],
    )
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=13),
        title_font=dict(size=18, color="#c4c4e0"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,30,47,0.6)",
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            zerolinecolor="rgba(255,255,255,0.08)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Quick stats beneath the chart
    col_data = df[selected_col].dropna()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Min", f"{col_data.min():,.2f}")
    s2.metric("Median", f"{col_data.median():,.2f}")
    s3.metric("Mean", f"{col_data.mean():,.2f}")
    s4.metric("Max", f"{col_data.max():,.2f}")
