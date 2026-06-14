"""
Streamlit dashboard — Theme 3: Smart Government — Malaysian Cost of Living AI.
Tabs: Overview | Time Series Forecast | State Clustering | Fuel Analysis
"""
import os
import sys
import json
import subprocess

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT_DIR      = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIGURES_DIR   = os.path.join(ROOT_DIR, "outputs", "figures")
MODELS_DIR    = os.path.join(ROOT_DIR, "outputs", "models")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
sys.path.insert(0, ROOT_DIR)

os.environ.setdefault("MPLCONFIGDIR", os.path.join(ROOT_DIR, "outputs", "mpl_cache"))

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Government — Malaysian CPI Analyser",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Global CSS — match HTML design ─────────────────────────────────────────
st.markdown("""
<style>
/* ── Force light theme / colour scheme ── */
html, body, [data-testid="stApp"] {
  background-color: #f4f6fa !important;
  color: #1e2330 !important;
  font-family: 'Segoe UI', system-ui, sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu,
header[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
footer { display: none !important; }

/* ── Main container ── */
.block-container {
  max-width: 1240px !important;
  margin: 0 auto !important;
  padding: 0 1.5rem 2rem !important;
}

/* ── Custom sticky header ── */
.app-header {
  background: #1a3c6e;
  color: #fff;
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0 -1.5rem 1.5rem -1.5rem;
  position: sticky;
  top: 0;
  z-index: 999;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}
.app-header-title { font-size: 1.2rem; font-weight: 700; line-height: 1.3; }
.app-header-sub   { font-size: 0.78rem; opacity: 0.75; margin-top: 2px; }

/* ── Tab navigation ── */
[data-baseweb="tab-list"] {
  background: #ffffff !important;
  border-bottom: 2px solid #d1d5db !important;
  gap: 0 !important;
  margin-bottom: 1.5rem !important;
}
button[data-testid="stTab"] {
  height: 48px !important;
  padding: 0 22px !important;
  background: transparent !important;
  border-radius: 0 !important;
  border-bottom: 3px solid transparent !important;
  margin-bottom: -2px !important;
}
button[data-testid="stTab"] p {
  font-size: 0.92rem !important;
  font-weight: 500 !important;
  color: #6b7280 !important;
  white-space: nowrap !important;
  margin: 0 !important;
}
button[data-testid="stTab"]:hover p { color: #1a3c6e !important; }
button[data-testid="stTab"][aria-selected="true"] {
  border-bottom: 3px solid #e8523a !important;
}
button[data-testid="stTab"][aria-selected="true"] p {
  color: #1a3c6e !important;
  font-weight: 700 !important;
}
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none !important; }

/* ── Metric stat boxes ── */
[data-testid="stMetric"] {
  background: #f4f6fa !important;
  border: 1px solid #d1d5db !important;
  border-radius: 8px !important;
  padding: 16px 20px !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.8rem !important;
  font-weight: 700 !important;
  color: #1a3c6e !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.78rem !important;
  color: #6b7280 !important;
  font-weight: 500 !important;
}

/* ── Card sections ── */
.card {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  padding: 24px;
  margin-bottom: 22px;
}
.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1a3c6e;
  text-align: center;
  margin: 0 0 6px 0;
}
.card-desc {
  font-size: 0.83rem;
  color: #6b7280;
  text-align: center;
  margin-bottom: 16px;
}

/* ── Headings ── */
h1, h2, h3 { color: #1a3c6e !important; }

/* ── Dividers ── */
hr { border-color: #d1d5db !important; margin: 1rem 0 !important; }

/* ── Captions / muted text ── */
[data-testid="stCaptionContainer"] p {
  color: #6b7280 !important;
  font-size: 0.83rem !important;
}

/* ── Primary button ── */
[data-testid="stButton"] > button[kind="primary"] {
  background: #e8523a !important;
  border-color: #e8523a !important;
  color: #fff !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
  opacity: 0.88 !important;
}

/* ── Not-ready banner ── */
.not-ready-banner {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 14px 20px;
  margin-bottom: 20px;
  font-size: 0.88rem;
  color: #92400e;
}

/* ── Tables ── */
[data-testid="stDataFrame"] thead th {
  background-color: #1a3c6e !important;
  color: #ffffff !important;
  font-weight: 600 !important;
}

/* ── Radio / select controls ── */
[data-testid="stRadio"] label { color: #1e2330 !important; }

/* ── Success message ── */
[data-testid="stAlert"][kind="success"] { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Data loaders (cached) ───────────────────────────────────────────────────
@st.cache_data
def load_arima() -> dict:
    with open(os.path.join(MODELS_DIR, "arima_results.json")) as f:
        return json.load(f)


@st.cache_data
def load_clustering() -> dict:
    with open(os.path.join(MODELS_DIR, "clustering_results.json")) as f:
        return json.load(f)


@st.cache_data
def load_fuel_correlation() -> dict | None:
    p = os.path.join(MODELS_DIR, "fuel_correlation.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


@st.cache_data
def load_df(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(PROCESSED_DIR, name))


def pipeline_ready() -> bool:
    return all(os.path.exists(p) for p in [
        os.path.join(MODELS_DIR, "arima_results.json"),
        os.path.join(MODELS_DIR, "clustering_results.json"),
        os.path.join(PROCESSED_DIR, "overall_inflation.csv"),
        os.path.join(PROCESSED_DIR, "states_kmeans_clustered.csv"),
        os.path.join(PROCESSED_DIR, "cpi_state_clean.csv"),
    ])


# ─── Malaysian state lat/lon ─────────────────────────────────────────────────
_STATE_LL: dict[str, tuple[float, float]] = {
    "Johor":             (1.86,  103.62),
    "Kedah":             (6.12,  100.37),
    "Kelantan":          (6.13,  102.24),
    "Melaka":            (2.19,  102.24),
    "Negeri Sembilan":   (2.72,  102.24),
    "Pahang":            (3.81,  103.33),
    "Penang":            (5.42,  100.33),
    "Perak":             (4.59,  101.09),
    "Perlis":            (6.44,  100.19),
    "Sabah":             (5.98,  116.07),
    "Sarawak":           (1.55,  110.36),
    "Selangor":          (3.07,  101.52),
    "Terengganu":        (5.31,  103.14),
    "W.P. Kuala Lumpur": (3.15,  101.69),
    "W.P. Labuan":       (5.28,  115.24),
    "W.P. Putrajaya":    (2.93,  101.69),
}

_PALETTE = [
    "#1a3c6e", "#e8523a", "#22c55e", "#a855f7",
    "#f59e0b", "#06b6d4", "#ec4899", "#84cc16",
    "#f97316", "#8b5cf6", "#14b8a6", "#ef4444",
]

_PLOTLY_COLORS = (
    px.colors.qualitative.Plotly
    + px.colors.qualitative.Pastel
    + px.colors.qualitative.Set3
)


def _add_coords(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["lat"] = df["state"].map(lambda s: _STATE_LL.get(s, (None, None))[0])
    df["lon"] = df["state"].map(lambda s: _STATE_LL.get(s, (None, None))[1])
    return df.dropna(subset=["lat", "lon"])


def _geo_layout(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    fig.update_geos(
        scope="asia",
        center={"lat": 4.0, "lon": 109.5},
        projection_scale=9,
        showland=True,  landcolor="WhiteSmoke",
        showocean=True, oceancolor="AliceBlue",
        showcoastlines=True, coastlinecolor="DarkGray",
    )
    fig.update_layout(
        title=title, height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(font_size=11),
    )
    return fig


def _card(title: str, desc: str = "") -> None:
    desc_html = f'<p class="card-desc">{desc}</p>' if desc else ""
    st.markdown(
        f'<div class="card"><p class="card-title">{title}</p>{desc_html}</div>',
        unsafe_allow_html=True,
    )


# ─── Pipeline runner ─────────────────────────────────────────────────────────
def _run_pipeline() -> None:
    script = os.path.join(ROOT_DIR, "run_pipeline.py")
    log_box = st.empty()
    lines: list[str] = []

    with st.status("Running Analysis Pipeline…", expanded=True) as status:
        proc = subprocess.Popen(
            [sys.executable, "-u", script, "--no-dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=ROOT_DIR,
        )
        for raw in proc.stdout:
            lines.append(raw.rstrip())
            log_box.code("\n".join(lines[-40:]))
        proc.wait()

        if proc.returncode == 0:
            status.update(label="Pipeline complete!", state="complete")
        else:
            status.update(
                label=f"Pipeline failed (exit code {proc.returncode})",
                state="error",
            )

    st.cache_data.clear()
    st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div style="display:flex;align-items:center;gap:14px;flex:1;min-width:0;">
    <span style="font-size:2rem;flex-shrink:0;">🏛</span>
    <div>
      <div class="app-header-title">
        🇲🇾 Smart Government — Malaysian CPI &amp; Cost of Living Analyser
      </div>
      <div class="app-header-sub">
        COS40007 Design Project 2026 · Theme 3 · DOSM Open Data
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Pipeline status + Run button (below header, above tabs) ─────────────────
ready = pipeline_ready()
col_status, col_btn = st.columns([5, 1])
with col_status:
    if not ready:
        st.markdown(
            '<div class="not-ready-banner">'
            '⚠ Pipeline outputs not found. Click <strong>▶ Run Analysis Pipeline</strong> '
            'to generate results.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.success("Pipeline outputs ready", icon="✅")
with col_btn:
    if st.button("▶  Run Analysis Pipeline", type="primary", use_container_width=True):
        _run_pipeline()

if not ready:
    st.stop()

# ─── Load data ───────────────────────────────────────────────────────────────
arima      = load_arima()
clust      = load_clustering()
fuel_corr  = load_fuel_correlation()
overall    = load_df("overall_inflation.csv")
cpi_div    = load_df("cpi_inflation_clean.csv")
fuel_df    = load_df("fuelprice_clean.csv")
kmeans_df  = load_df("states_kmeans_clustered.csv")
hier_df    = load_df("states_hierarchical_clustered.csv")

overall["date"]  = pd.to_datetime(overall["date"])
cpi_div["date"]  = pd.to_datetime(cpi_div["date"])
fuel_df["date"]  = pd.to_datetime(fuel_df["date"])

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Overview",
    "📈  Time Series Forecast",
    "🗂  State Clustering",
    "⛽  Fuel Analysis",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Project summary card ─────────────────────────────────────────────────
    st.markdown("""
    <div class="card" style="text-align:center;">
      <p class="card-title">Project Summary</p>
      <p class="card-desc">
        This system analyses Malaysia's Consumer Price Index (CPI) inflation across
        13 divisions and 16 states, applying <strong>ARIMA time series forecasting</strong>
        on the national inflation trend and <strong>K-Means clustering</strong> to group
        states by their CPI and income profile. Fuel price dynamics and their correlation
        with inflation are also examined. Data sourced from the Department of Statistics
        Malaysia (DOSM) open data portal.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Key stat boxes ───────────────────────────────────────────────────────
    latest_row  = overall.sort_values("date").iloc[-1]
    latest_fuel = fuel_df.dropna(subset=["avg_fuel"]).sort_values("date").iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest YoY Inflation",  f"{latest_row['inflation_yoy']:.2f}%",
              help="Most recent year-on-year CPI inflation")
    c2.metric("Latest MoM Inflation",  f"{latest_row['inflation_mom']:.2f}%",
              help="Most recent month-on-month CPI inflation")
    c3.metric("Avg Fuel Price (latest)", f"RM {latest_fuel['avg_fuel']:.2f}",
              help="Average of RON95, RON97, Diesel (most recent month)")
    c4.metric("Series Coverage",
              f"{overall['date'].min().year}–{overall['date'].max().year}",
              help="Overall inflation series date range")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── National inflation trend ─────────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">National CPI Inflation — Last 5 Years</p>
      <p class="card-desc">
        Year-on-year (YoY) and month-on-month (MoM) national CPI inflation.
        Green fill indicates deflation.
      </p>
    </div>
    """, unsafe_allow_html=True)

    unit  = st.radio("Inflation unit", ["Year-on-Year (%)", "Month-on-Month (%)"],
                     horizontal=True, key="ov_unit")
    y_col = "inflation_yoy" if "Year" in unit else "inflation_mom"
    y_lbl = "YoY Inflation (%)" if "Year" in unit else "MoM Inflation (%)"

    cutoff5 = overall["date"].max() - pd.DateOffset(years=5)
    recent5 = overall[overall["date"] >= cutoff5].sort_values("date")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=recent5["date"], y=recent5[y_col],
        mode="lines", name=y_lbl,
        line=dict(color="#1a3c6e", width=2.5),
        fill="tozeroy", fillcolor="rgba(26,60,110,0.08)",
    ))
    fig_trend.add_hline(y=0, line_dash="dot", line_color="#9ca3af", line_width=1)
    fig_trend.update_layout(
        xaxis_title="Date", yaxis_title=y_lbl,
        height=360, margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        xaxis=dict(showspikes=True, spikecolor="#94a3b8", spikesnap="cursor",
                   spikedash="solid", spikewidth=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Division inflation trends ────────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">CPI Inflation by Division — Last 3 Years</p>
      <p class="card-desc">
        Year-on-year inflation trends broken down by all 13 DOSM CPI divisions.
        Divisions cover food, housing, transport, health, education, and more.
      </p>
    </div>
    """, unsafe_allow_html=True)

    cutoff3 = cpi_div["date"].max() - pd.DateOffset(years=3)
    div_rec = cpi_div[cpi_div["date"] >= cutoff3].dropna(subset=["inflation_yoy"])
    divisions = sorted([d for d in div_rec["division"].unique() if d != "overall"])

    fig_div = go.Figure()
    for i, div in enumerate(divisions):
        grp   = div_rec[div_rec["division"] == div].sort_values("date")
        label = grp["division_label"].iloc[0] if "division_label" in grp.columns else div
        fig_div.add_trace(go.Scatter(
            x=grp["date"], y=grp["inflation_yoy"],
            mode="lines", name=label,
            line=dict(width=1.6, color=_PLOTLY_COLORS[i % len(_PLOTLY_COLORS)]),
        ))
    ovr = div_rec[div_rec["division"] == "overall"].sort_values("date")
    if not ovr.empty:
        fig_div.add_trace(go.Scatter(
            x=ovr["date"], y=ovr["inflation_yoy"],
            mode="lines", name="Overall CPI",
            line=dict(color="#000", width=2.5),
        ))
    fig_div.add_hline(y=0, line_dash="dot", line_color="#9ca3af", line_width=1)
    fig_div.update_layout(
        xaxis_title="Date", yaxis_title="YoY Inflation (%)",
        height=460, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(font_size=10, x=1.01, y=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig_div, use_container_width=True)

    # ── State CPI comparison ─────────────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">State CPI Index Explorer</p>
      <p class="card-desc">
        Monthly overall CPI index for selected states (2010–present).
        Base year: 2010 = 100. A rising index indicates cumulative price growth.
      </p>
    </div>
    """, unsafe_allow_html=True)

    cpi_state = load_df("cpi_state_clean.csv")
    cpi_state["date"] = pd.to_datetime(cpi_state["date"])
    all_states = sorted(cpi_state["state"].unique().tolist())

    sel_states = st.multiselect(
        "Select states to compare", all_states,
        default=all_states[:5] if len(all_states) >= 5 else all_states,
        key="ov_state_sel",
    )
    if sel_states:
        fig_st = go.Figure()
        for i, state in enumerate(sel_states):
            grp = cpi_state[
                (cpi_state["state"] == state) & (cpi_state["division"] == "overall")
            ].sort_values("date")
            fig_st.add_trace(go.Scatter(
                x=grp["date"], y=grp["index"],
                mode="lines", name=state,
                line=dict(width=1.8, color=_PLOTLY_COLORS[i % len(_PLOTLY_COLORS)]),
            ))
        fig_st.update_layout(
            xaxis_title="Date", yaxis_title="CPI Index (Base 2010 = 100)",
            height=380, margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            hovermode="x unified",
        )
        st.plotly_chart(fig_st, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TIME SERIES FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    order = arima.get("arima_order", ["?", "?", "?"])
    m     = arima.get("metrics", {})

    # ── Forecast card ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="card">
      <p class="card-title">ARIMA National Inflation Forecast</p>
      <p class="card-desc">
        ARIMA fitted on monthly national CPI year-on-year inflation (overall division, 1981–present).
        Order selected via BIC grid search; stationarity verified with the Augmented Dickey-Fuller test.
        The model is evaluated on a held-out 24-month test window before forecasting.
      </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ARIMA Order",  f"({order[0]},{order[1]},{order[2]})")
    c2.metric("Test MAE",     f"{m['MAE']:.4f}"    if m.get("MAE")  else "—")
    c3.metric("Test RMSE",    f"{m['RMSE']:.4f}"   if m.get("RMSE") else "—")
    c4.metric("BIC",          f"{arima['bic']:.1f}" if arima.get("bic") else "—")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Forecast chart ───────────────────────────────────────────────────────
    train_dates = pd.to_datetime(arima["train"]["dates"])
    train_vals  = np.array(arima["train"]["values"])
    cutoff10    = train_dates.max() - pd.DateOffset(years=10)
    mask10      = train_dates >= cutoff10

    test_dates = pd.to_datetime(arima["test"]["dates"])
    fc_dates   = pd.to_datetime(arima["forecast"]["dates"])
    fc_lower   = list(arima["forecast"]["lower"])
    fc_upper   = list(arima["forecast"]["upper"])
    fc_dates_l = list(fc_dates)

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        x=train_dates[mask10], y=train_vals[mask10],
        mode="lines", name="Historical (train)",
        line=dict(color="#1a3c6e", width=1.5),
    ))
    fig_fc.add_trace(go.Scatter(
        x=test_dates, y=arima["test"]["actual"],
        mode="lines+markers", name="Actual (test)",
        marker=dict(size=5, color="#22c55e"),
        line=dict(color="#22c55e", width=2),
    ))
    fig_fc.add_trace(go.Scatter(
        x=test_dates, y=arima["test"]["predicted"],
        mode="lines+markers", name="Predicted (test)",
        marker=dict(size=5, color="#ef4444", symbol="diamond"),
        line=dict(color="#ef4444", dash="dash", width=2),
    ))
    fig_fc.add_trace(go.Scatter(
        x=fc_dates_l + fc_dates_l[::-1],
        y=fc_upper + fc_lower[::-1],
        fill="toself", fillcolor="rgba(168,85,247,0.13)",
        line=dict(color="rgba(0,0,0,0)"),
        name="95% CI", hoverinfo="skip",
    ))
    fig_fc.add_trace(go.Scatter(
        x=fc_dates, y=arima["forecast"]["values"],
        mode="lines+markers", name=f"Forecast ({len(fc_dates)}m)",
        marker=dict(size=6, symbol="triangle-up", color="#a855f7"),
        line=dict(color="#a855f7", dash="dot", width=2.5),
    ))
    fig_fc.add_hline(y=0, line_dash="dot", line_color="#9ca3af", line_width=0.8)
    fig_fc.add_vline(
        x=str(test_dates[0].date()),
        line_dash="dot", line_color="#9ca3af", line_width=1,
        annotation_text="test split", annotation_position="top left",
        annotation_font_size=10,
    )
    fig_fc.update_layout(
        title=f"National CPI Inflation Forecast — ARIMA({order[0]},{order[1]},{order[2]})",
        xaxis_title="Date", yaxis_title="CPI Inflation YoY (%)",
        height=480, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.22),
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # ── Evaluation metrics table ─────────────────────────────────────────────
    ts_metrics_csv = os.path.join(MODELS_DIR, "ts_metrics_summary.csv")
    if os.path.exists(ts_metrics_csv):
        st.markdown("""
        <div class="card">
          <p class="card-title">Evaluation Metrics</p>
          <p class="card-desc">ARIMA performance on the held-out 24-month test set.</p>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(pd.read_csv(ts_metrics_csv), use_container_width=True, hide_index=True)

    # ── Division trends figure ───────────────────────────────────────────────
    div_trends_png = os.path.join(FIGURES_DIR, "ts_division_trends.png")
    if os.path.exists(div_trends_png):
        with st.expander("CPI Division Inflation Trends (pre-generated figure)"):
            st.image(div_trends_png, use_container_width=True)

    # ── Live ARIMA ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">Live ARIMA Forecast</p>
      <p class="card-desc">
        Re-run ARIMA with a custom forecast horizon using the pre-computed order and model.
      </p>
    </div>
    """, unsafe_allow_html=True)

    horizon = st.slider("Forecast horizon (months)", 6, 48, 24, key="live_horizon")
    if st.button("↺  Run Forecast", type="primary", key="live_run"):
        with st.spinner("Computing forecast…"):
            from src.time_series import run_live

            inf_df = load_df("overall_inflation.csv").copy()
            inf_df["date"] = pd.to_datetime(inf_df["date"])

            order_list    = arima.get("arima_order") or arima.get("order")
            precomp_order = tuple(int(x) for x in order_list) if order_list else None

            result_event: dict | None = None
            for event in run_live(inf_df, horizon=horizon,
                                  order=precomp_order, precomputed=arima):
                if event.get("type") == "result":
                    result_event = event

        if result_event:
            fc2      = result_event
            h_dates  = pd.to_datetime(fc2["train"]["dates"])
            h_vals   = np.array(fc2["train"]["values"])
            cut_live = h_dates.max() - pd.DateOffset(years=5)
            m_live   = h_dates >= cut_live
            fc2d     = pd.to_datetime(fc2["forecast"]["dates"])
            fc2dl    = list(fc2d)

            fig_live = go.Figure()
            fig_live.add_trace(go.Scatter(
                x=h_dates[m_live], y=h_vals[m_live],
                mode="lines", name="Historical",
                line=dict(color="#1a3c6e", width=1.5),
            ))
            fig_live.add_trace(go.Scatter(
                x=fc2d, y=fc2["forecast"]["values"],
                mode="lines+markers", name=f"Forecast ({horizon}m)",
                marker=dict(size=5, symbol="triangle-up", color="#a855f7"),
                line=dict(color="#a855f7", width=2),
            ))
            fig_live.add_trace(go.Scatter(
                x=fc2dl + fc2dl[::-1],
                y=list(fc2["forecast"]["upper"]) + list(fc2["forecast"]["lower"])[::-1],
                fill="toself", fillcolor="rgba(168,85,247,0.13)",
                line=dict(color="rgba(0,0,0,0)"), name="95% CI",
            ))
            fig_live.add_hline(y=0, line_dash="dot", line_color="#9ca3af", line_width=0.8)
            fig_live.update_layout(
                title=f"Live ARIMA — {horizon}-Month Forecast",
                xaxis_title="Date", yaxis_title="Inflation YoY (%)",
                height=380, margin=dict(l=0, r=0, t=40, b=0),
                plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            )
            st.plotly_chart(fig_live, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CLUSTERING
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="card">
      <p class="card-title">State Cluster Explorer</p>
      <p class="card-desc">
        16 Malaysian states clustered by 5 features: mean CPI index, CPI volatility,
        CPI growth rate, latest mean household income, and latest median household income.
        Optimal k selected via Silhouette score.
      </p>
    </div>
    """, unsafe_allow_html=True)

    method      = st.radio("Clustering method", ["K-Means", "Hierarchical"],
                           horizontal=True, key="cl_method")
    cluster_df  = kmeans_df  if method == "K-Means" else hier_df
    cluster_col = "kmeans_cluster" if method == "K-Means" else "hier_cluster"

    # ── Cluster assignment table ─────────────────────────────────────────────
    disp_cols = [c for c in cluster_df.columns if c.lower() not in ("lat", "lon")]
    st.dataframe(cluster_df[disp_cols], use_container_width=True, hide_index=True)

    # ── Cluster map ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">Malaysia State Cluster Map</p>
      <p class="card-desc">
        Geographic distribution of cluster assignments across all 16 Malaysian states.
        Each state is coloured by its cluster. Hover for income and CPI details.
      </p>
    </div>
    """, unsafe_allow_html=True)

    if cluster_col in cluster_df.columns:
        map_df = _add_coords(cluster_df)
        if not map_df.empty:
            map_df["Cluster"] = map_df[cluster_col].astype(str)
            hover_extra = {c: True for c in disp_cols if c not in ("state", cluster_col)}
            fig_map = px.scatter_geo(
                map_df, lat="lat", lon="lon",
                color="Cluster", hover_name="state", hover_data=hover_extra,
                size_max=20, opacity=0.88,
                color_discrete_sequence=_PALETTE,
            )
            _geo_layout(fig_map, f"{method} Cluster Map — Malaysian States")
            fig_map.update_layout(paper_bgcolor="#ffffff")
            st.plotly_chart(fig_map, use_container_width=True)

    # ── Elbow + PCA figures ──────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="card"><p class="card-title">Elbow + Silhouette Method</p></div>',
                    unsafe_allow_html=True)
        p = os.path.join(FIGURES_DIR, "cluster_elbow_silhouette.png")
        if os.path.exists(p):
            st.image(p, use_container_width=True)
    with col_b:
        pca_file = "cluster_pca_kmeans.png" if method == "K-Means" else "cluster_pca_hierarchical.png"
        st.markdown(f'<div class="card"><p class="card-title">{method} — PCA Projection</p></div>',
                    unsafe_allow_html=True)
        p = os.path.join(FIGURES_DIR, pca_file)
        if os.path.exists(p):
            st.image(p, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="card"><p class="card-title">Hierarchical Clustering — Dendrogram</p></div>',
                    unsafe_allow_html=True)
        p = os.path.join(FIGURES_DIR, "cluster_dendrogram.png")
        if os.path.exists(p):
            st.image(p, use_container_width=True)
    with col_d:
        st.markdown('<div class="card"><p class="card-title">Cluster Socioeconomic Profiles</p></div>',
                    unsafe_allow_html=True)
        p = os.path.join(FIGURES_DIR, "cluster_profiles.png")
        if os.path.exists(p):
            st.image(p, use_container_width=True)

    # ── Clustering evaluation metrics ────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">Clustering Evaluation Metrics</p>
      <p class="card-desc">
        Comparison of K-Means and Hierarchical (Ward linkage) clustering quality.
        Higher Silhouette and Calinski-Harabász are better; lower Davies-Bouldin is better.
      </p>
    </div>
    """, unsafe_allow_html=True)

    cm_path = os.path.join(MODELS_DIR, "cluster_metrics_summary.csv")
    if os.path.exists(cm_path):
        st.dataframe(pd.read_csv(cm_path), use_container_width=True, hide_index=True)

    # ── Elbow metrics table ──────────────────────────────────────────────────
    elbow = clust.get("elbow_metrics", {})
    if elbow:
        st.markdown("""
        <div class="card">
          <p class="card-title">Elbow / Silhouette / Davies-Bouldin Metrics</p>
        </div>
        """, unsafe_allow_html=True)
        k_range = elbow.get("k_range", [])
        if k_range:
            elbw_df = pd.DataFrame({
                "K":              k_range,
                "Inertia":        elbow.get("inertias",    [None] * len(k_range)),
                "Silhouette":     elbow.get("silhouettes", [None] * len(k_range)),
                "Davies-Bouldin": elbow.get("db_scores",   [None] * len(k_range)),
            })
            st.dataframe(elbw_df, use_container_width=True, hide_index=True)
        best_k = clust.get("best_k")
        if best_k:
            st.success(f"Selected K = {best_k}  (best silhouette score)", icon="✅")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FUEL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    # ── Fuel price trend ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="card">
      <p class="card-title">Retail Fuel Prices — Monthly Average</p>
      <p class="card-desc">
        Monthly retail prices for RON95, RON97, and Diesel in RM per litre (2017–present).
        Data resampled from weekly pump prices reported by DOSM.
      </p>
    </div>
    """, unsafe_allow_html=True)

    fuel_plot = fuel_df.dropna(subset=["ron95"]).sort_values("date")
    fig_fuel  = go.Figure()
    for col, label, color in [
        ("ron95",    "RON 95",  "#1a3c6e"),
        ("ron97",    "RON 97",  "#e8523a"),
        ("diesel",   "Diesel",  "#22c55e"),
        ("avg_fuel", "Average", "#9ca3af"),
    ]:
        if col in fuel_plot.columns:
            fig_fuel.add_trace(go.Scatter(
                x=fuel_plot["date"], y=fuel_plot[col],
                mode="lines", name=label,
                line=dict(color=color, width=1.8,
                          dash="dot" if col == "avg_fuel" else "solid"),
            ))
    fig_fuel.update_layout(
        xaxis_title="Date", yaxis_title="Price (RM / litre)",
        height=380, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        hovermode="x unified", legend=dict(orientation="h", y=-0.22),
    )
    st.plotly_chart(fig_fuel, use_container_width=True)

    # ── Fuel-inflation correlation ────────────────────────────────────────────
    if fuel_corr:
        st.markdown("""
        <div class="card">
          <p class="card-title">Fuel-Inflation Correlation Analysis</p>
          <p class="card-desc">
            Pearson correlation between monthly fuel prices and national CPI YoY inflation.
            <strong>Contemporaneous:</strong> same month.
            <strong>Lag-1:</strong> fuel price leads inflation by one month.
          </p>
        </div>
        """, unsafe_allow_html=True)

        corr   = fuel_corr["correlations"]
        labels = [k.upper() for k in corr]
        contemp = [corr[k].get("contemporaneous", 0) for k in corr]
        lag1    = [corr[k].get("lag1", 0) for k in corr]

        fig_corr = go.Figure()
        fig_corr.add_trace(go.Bar(
            name="Contemporaneous (r)", x=labels, y=contemp,
            marker_color=["#1a3c6e" if v >= 0 else "#e8523a" for v in contemp],
            opacity=0.85,
        ))
        fig_corr.add_trace(go.Bar(
            name="Lag-1 month (r)", x=labels, y=lag1,
            marker_color=["#a855f7" if v >= 0 else "#f59e0b" for v in lag1],
            opacity=0.85,
        ))
        fig_corr.add_hline(y=0, line_color="#9ca3af", line_width=1)
        fig_corr.update_layout(
            title="Pearson r — Fuel Prices vs National CPI Inflation",
            xaxis_title="Fuel Type", yaxis_title="Pearson r",
            yaxis_range=[-1, 1], barmode="group",
            height=360, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            legend=dict(orientation="h", y=-0.22),
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        st.caption(
            f"Based on {fuel_corr['n_overlap_months']} overlapping months "
            f"({fuel_corr['overlap_start']} → {fuel_corr['overlap_end']})"
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── ARIMAX experiment ─────────────────────────────────────────────────────
    exog_exp = arima.get("fuel_exog_experiment", {})
    if exog_exp.get("available"):
        st.markdown("""
        <div class="card">
          <p class="card-title">Does Fuel Improve Inflation Prediction? (ARIMAX vs ARIMA)</p>
          <p class="card-desc">
            Correlation shows association; this tests <strong>predictive value</strong>.
            Two models are fit on the fuel/CPI overlap window and evaluated on the same
            held-out test period. A lower RMSE for ARIMAX means fuel adds genuine
            forecasting signal.
          </p>
        </div>
        """, unsafe_allow_html=True)

        ex_m = exog_exp.get("arimax_metrics", {})
        ar_m = exog_exp.get("arima_metrics",  {})
        pct  = exog_exp.get("rmse_improvement_pct", 0.0)

        c1, c2, c3 = st.columns(3)
        c1.metric("ARIMAX RMSE",           f"{ex_m['RMSE']:.4f}" if ex_m.get("RMSE") else "—")
        c2.metric("Univariate ARIMA RMSE", f"{ar_m['RMSE']:.4f}" if ar_m.get("RMSE") else "—")
        c3.metric("RMSE Improvement", f"{pct:+.2f}%",
                  help="Positive = ARIMAX beats univariate ARIMA; negative = univariate wins")

        fig_exog = go.Figure()
        fig_exog.add_trace(go.Bar(
            name="ARIMAX (with fuel)", x=["RMSE", "MAE", "MASE"],
            y=[ex_m.get("RMSE"), ex_m.get("MAE"), ex_m.get("MASE")],
            marker_color="#1a3c6e",
            text=[f"{v:.4f}" if v else "" for v in [ex_m.get("RMSE"), ex_m.get("MAE"), ex_m.get("MASE")]],
            textposition="auto",
        ))
        fig_exog.add_trace(go.Bar(
            name="ARIMA (univariate)", x=["RMSE", "MAE", "MASE"],
            y=[ar_m.get("RMSE"), ar_m.get("MAE"), ar_m.get("MASE")],
            marker_color="#e8523a", opacity=0.8,
            text=[f"{v:.4f}" if v else "" for v in [ar_m.get("RMSE"), ar_m.get("MAE"), ar_m.get("MASE")]],
            textposition="auto",
        ))
        fig_exog.update_layout(
            title="Test-set error: fuel-augmented vs univariate (lower = better)",
            yaxis_title="Error", barmode="group",
            height=340, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            legend=dict(orientation="h", y=-0.22),
        )
        st.plotly_chart(fig_exog, use_container_width=True)

        coefs = exog_exp.get("exog_coefficients", {})
        if coefs:
            st.markdown('<p class="card-title" style="color:#1a3c6e;font-weight:700;">'
                        'Fuel Price Coefficient (full-window refit)</p>', unsafe_allow_html=True)
            coef_rows = [
                {
                    "Variable":               col,
                    "Coefficient":            vals.get("coef"),
                    "p-value":                vals.get("pvalue"),
                    "Significant (p<0.05)":   "Yes" if (vals.get("pvalue") or 1.0) < 0.05 else "No",
                }
                for col, vals in coefs.items()
            ]
            st.dataframe(pd.DataFrame(coef_rows), use_container_width=True, hide_index=True)

        st.caption(
            f"ARIMAX order {tuple(exog_exp.get('order', []))} · "
            f"test horizon {exog_exp.get('test_months')} months · "
            f"{exog_exp.get('n_overlap_months', '?')} overlapping months used."
        )

    elif exog_exp:
        st.info(f"ARIMAX experiment not available: {exog_exp.get('reason', 'unknown reason')}")
    else:
        st.info("ARIMAX experiment data not found — re-run the pipeline.")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; font-size:0.75rem; color:#6b7280;
            padding:24px 0 12px 0; margin-top:20px;
            border-top:1px solid #d1d5db;">
  Data source: Department of Statistics Malaysia (DOSM) · CC BY 4.0 ·
  COS40007 Design Project 2026
</div>
""", unsafe_allow_html=True)
