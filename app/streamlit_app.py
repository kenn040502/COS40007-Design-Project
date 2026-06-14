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

os.environ.setdefault(
    "MPLCONFIGDIR",
    os.path.join(ROOT_DIR, "outputs", "mpl_cache"),
)

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Government — Malaysian CPI Analyser",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; padding-bottom: 1.5rem; }
  [data-testid="stMetricValue"] { font-size: 1.55rem !important; }

  /* ── Tab navigation bar ── */
  .stTabs [data-baseweb="tab-list"] {
      gap: 6px;
      border-bottom: 2px solid #d1d5db;
      padding-bottom: 0;
      margin-bottom: 1rem;
  }
  .stTabs [data-baseweb="tab"] {
      height: 44px;
      padding: 0 22px;
      font-size: 0.95rem;
      font-weight: 500;
      color: #6b7280;
      background: transparent;
      border: none;
      border-bottom: 3px solid transparent;
      border-radius: 0;
      white-space: nowrap;
  }
  .stTabs [data-baseweb="tab"]:hover {
      color: #1a3c6e;
      background: rgba(26,60,110,0.04);
  }
  .stTabs [aria-selected="true"] {
      color: #1a3c6e !important;
      border-bottom: 3px solid #e8523a !important;
      font-weight: 700 !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none; }
  .stTabs [data-baseweb="tab-border"]    { display: none; }
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


# ─── Malaysian state lat/lon (scatter-geo map) ───────────────────────────────
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
        title=title,
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(font_size=11),
    )
    return fig


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

    # Invalidate caches so the dashboard reloads fresh outputs
    st.cache_data.clear()
    st.rerun()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏛 Smart Government")
    st.caption("Malaysian CPI & Cost of Living AI")
    st.divider()

    ready = pipeline_ready()
    if ready:
        st.success("Pipeline outputs ready", icon="✅")
    else:
        st.warning("Pipeline not yet run", icon="⚠️")

    if st.button("▶  Run Analysis Pipeline", type="primary", use_container_width=True):
        _run_pipeline()

    st.divider()
    st.caption("COS40007 Design Project 2026 · Theme 3")

# ─── Guard ───────────────────────────────────────────────────────────────────
if not pipeline_ready():
    st.title("🇲🇾 Smart Government — Malaysian CPI & Cost of Living Analyser")
    st.info(
        "Click **▶ Run Analysis Pipeline** in the sidebar to generate results.",
        icon="ℹ️",
    )
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
    st.subheader("🇲🇾 National Overview — Malaysian Cost of Living")
    st.caption(
        "Consumer Price Index (CPI) inflation across 13 divisions and 16 states. "
        "Data sourced from the Department of Statistics Malaysia (DOSM) open data portal."
    )

    # Key metric cards
    latest_row   = overall.sort_values("date").iloc[-1]
    latest_fuel  = fuel_df.dropna(subset=["avg_fuel"]).sort_values("date").iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Latest YoY Inflation",
        f"{latest_row['inflation_yoy']:.2f}%",
        help="Most recent year-on-year CPI inflation",
    )
    c2.metric(
        "Latest MoM Inflation",
        f"{latest_row['inflation_mom']:.2f}%",
        help="Most recent month-on-month CPI inflation",
    )
    c3.metric(
        "Avg Fuel Price (latest)",
        f"RM {latest_fuel['avg_fuel']:.2f}",
        help="Average of RON95, RON97, Diesel (most recent month)",
    )
    c4.metric(
        "Series Coverage",
        f"{overall['date'].min().year}–{overall['date'].max().year}",
        help="Overall inflation series date range",
    )

    st.divider()

    # ── Inflation trend ──────────────────────────────────────────────────────
    unit = st.radio(
        "Inflation unit",
        ["Year-on-Year (%)", "Month-on-Month (%)"],
        horizontal=True,
        key="ov_unit",
    )
    y_col = "inflation_yoy" if "Year" in unit else "inflation_mom"
    y_lbl = "YoY Inflation (%)"  if "Year" in unit else "MoM Inflation (%)"

    cutoff5 = overall["date"].max() - pd.DateOffset(years=5)
    recent5 = overall[overall["date"] >= cutoff5].sort_values("date")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=recent5["date"], y=recent5[y_col],
        mode="lines", name=y_lbl,
        line=dict(color="#1a3c6e", width=2),
        fill="tozeroy", fillcolor="rgba(26,60,110,0.08)",
    ))
    fig_trend.add_hline(y=0, line_dash="dot", line_color="gray", line_width=0.8)
    fig_trend.update_layout(
        title="National CPI Inflation — Last 5 Years",
        xaxis_title="Date", yaxis_title=y_lbl,
        height=340, margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Division inflation trends ────────────────────────────────────────────
    cutoff3   = cpi_div["date"].max() - pd.DateOffset(years=3)
    div_rec   = cpi_div[cpi_div["date"] >= cutoff3].dropna(subset=["inflation_yoy"])
    divisions = sorted([d for d in div_rec["division"].unique() if d != "overall"])

    fig_div = go.Figure()
    for i, div in enumerate(divisions):
        grp   = div_rec[div_rec["division"] == div].sort_values("date")
        label = grp["division_label"].iloc[0] if "division_label" in grp.columns else div
        fig_div.add_trace(go.Scatter(
            x=grp["date"], y=grp["inflation_yoy"],
            mode="lines", name=label,
            line=dict(width=1.4, color=_PLOTLY_COLORS[i % len(_PLOTLY_COLORS)]),
        ))
    ovr = div_rec[div_rec["division"] == "overall"].sort_values("date")
    if not ovr.empty:
        fig_div.add_trace(go.Scatter(
            x=ovr["date"], y=ovr["inflation_yoy"],
            mode="lines", name="Overall CPI",
            line=dict(color="black", width=2.5),
        ))
    fig_div.add_hline(y=0, line_dash="dot", line_color="gray", line_width=0.8)
    fig_div.update_layout(
        title="CPI Inflation by Division — Last 3 Years",
        xaxis_title="Date", yaxis_title="YoY Inflation (%)",
        height=420, margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(font_size=10),
    )
    st.plotly_chart(fig_div, use_container_width=True)

    # ── State CPI comparison ─────────────────────────────────────────────────
    st.subheader("State CPI Trend Comparison")
    cpi_state = load_df("cpi_state_clean.csv")
    cpi_state["date"] = pd.to_datetime(cpi_state["date"])
    all_states = sorted(cpi_state["state"].unique().tolist())

    sel_states = st.multiselect(
        "Select states to compare",
        all_states,
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
            title="Overall CPI Index by State",
            xaxis_title="Date", yaxis_title="CPI Index",
            height=380, margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_st, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TIME SERIES FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("ARIMA National CPI Inflation Forecast")

    order = arima.get("arima_order", ["?", "?", "?"])
    m     = arima.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ARIMA Order", f"({order[0]},{order[1]},{order[2]})")
    c2.metric("Test MAE",    f"{m['MAE']:.4f}"  if m.get("MAE")  else "—")
    c3.metric("Test RMSE",   f"{m['RMSE']:.4f}" if m.get("RMSE") else "—")
    c4.metric("BIC",         f"{arima['bic']:.1f}" if arima.get("bic") else "—")

    # ── Forecast chart (rebuilt from JSON) ───────────────────────────────────
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
        mode="lines", name="Historical",
        line=dict(color="steelblue", width=1.5),
    ))
    fig_fc.add_trace(go.Scatter(
        x=test_dates, y=arima["test"]["actual"],
        mode="lines+markers", name="Actual (test)",
        marker=dict(size=4), line=dict(color="seagreen", width=1.5),
    ))
    fig_fc.add_trace(go.Scatter(
        x=test_dates, y=arima["test"]["predicted"],
        mode="lines+markers", name="Predicted (test)",
        marker=dict(size=4), line=dict(color="crimson", width=1.5, dash="dash"),
    ))
    fig_fc.add_trace(go.Scatter(
        x=fc_dates, y=arima["forecast"]["values"],
        mode="lines+markers", name=f"Forecast ({len(fc_dates)}m)",
        marker=dict(size=4, symbol="triangle-up"),
        line=dict(color="mediumpurple", width=2),
    ))
    fig_fc.add_trace(go.Scatter(
        x=fc_dates_l + fc_dates_l[::-1],
        y=fc_upper + fc_lower[::-1],
        fill="toself", fillcolor="rgba(147,112,219,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name="95% CI", showlegend=True,
    ))
    fig_fc.add_hline(y=0, line_dash="dot", line_color="gray", line_width=0.8)
    fig_fc.add_vline(
        x=str(test_dates[0].date()),
        line_dash="dot", line_color="gray", line_width=1,
        annotation_text="test start", annotation_position="top left",
    )
    fig_fc.update_layout(
        title=f"ARIMA({order[0]},{order[1]},{order[2]}) — Historical + {len(fc_dates)}-Month Forecast",
        xaxis_title="Date", yaxis_title="Inflation YoY (%)",
        height=430, margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # ── Static division trends figure ────────────────────────────────────────
    div_trends_png = os.path.join(FIGURES_DIR, "ts_division_trends.png")
    if os.path.exists(div_trends_png):
        with st.expander("CPI Division Inflation Trends (pre-generated figure)"):
            st.image(div_trends_png, use_container_width=True)

    # ── Metrics summary table ────────────────────────────────────────────────
    ts_metrics_csv = os.path.join(MODELS_DIR, "ts_metrics_summary.csv")
    if os.path.exists(ts_metrics_csv):
        st.subheader("Evaluation Metrics Summary")
        st.dataframe(
            pd.read_csv(ts_metrics_csv),
            use_container_width=True,
            hide_index=True,
        )

    # ── Live ARIMA ───────────────────────────────────────────────────────────
    st.subheader("Live ARIMA Forecast")
    st.caption("Re-run ARIMA with a custom forecast horizon (uses pre-computed order & model).")

    horizon = st.slider("Forecast horizon (months)", 6, 48, 24, key="live_horizon")

    if st.button("Run Live Forecast", key="live_run"):
        with st.spinner("Computing forecast…"):
            from src.time_series import run_live

            inf_df = load_df("overall_inflation.csv").copy()
            inf_df["date"] = pd.to_datetime(inf_df["date"])

            order_list = arima.get("arima_order") or arima.get("order")
            precomp_order = tuple(int(x) for x in order_list) if order_list else None

            result_event: dict | None = None
            for event in run_live(inf_df, horizon=horizon,
                                  order=precomp_order, precomputed=arima):
                if event.get("type") == "result":
                    result_event = event

        if result_event:
            fc2       = result_event
            h_dates   = pd.to_datetime(fc2["train"]["dates"])
            h_vals    = np.array(fc2["train"]["values"])
            cut_live  = h_dates.max() - pd.DateOffset(years=5)
            m_live    = h_dates >= cut_live
            fc2_dates = pd.to_datetime(fc2["forecast"]["dates"])
            fc2_dl    = list(fc2_dates)
            fc2_low   = list(fc2["forecast"]["lower"])
            fc2_up    = list(fc2["forecast"]["upper"])

            fig_live = go.Figure()
            fig_live.add_trace(go.Scatter(
                x=h_dates[m_live], y=h_vals[m_live],
                mode="lines", name="Historical",
                line=dict(color="steelblue", width=1.5),
            ))
            fig_live.add_trace(go.Scatter(
                x=fc2_dates, y=fc2["forecast"]["values"],
                mode="lines+markers", name=f"Forecast ({horizon}m)",
                marker=dict(size=4, symbol="triangle-up"),
                line=dict(color="mediumpurple", width=2),
            ))
            fig_live.add_trace(go.Scatter(
                x=fc2_dl + fc2_dl[::-1],
                y=fc2_up + fc2_low[::-1],
                fill="toself", fillcolor="rgba(147,112,219,0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name="95% CI",
            ))
            fig_live.add_hline(y=0, line_dash="dot", line_color="gray", line_width=0.8)
            fig_live.update_layout(
                title=f"Live ARIMA — {horizon}-Month Forecast",
                xaxis_title="Date", yaxis_title="Inflation YoY (%)",
                height=380, margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(fig_live, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CLUSTERING
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Malaysian State Clustering")

    method     = st.radio(
        "Clustering method", ["K-Means", "Hierarchical"],
        horizontal=True, key="cl_method",
    )
    cluster_df  = kmeans_df  if method == "K-Means" else hier_df
    cluster_col = "kmeans_cluster" if method == "K-Means" else "hier_cluster"

    # ── Cluster assignment table ─────────────────────────────────────────────
    st.subheader("State Cluster Assignments")
    disp_cols = [c for c in cluster_df.columns if c.lower() not in ("lat", "lon")]
    st.dataframe(cluster_df[disp_cols], use_container_width=True, hide_index=True)

    # ── Cluster map ──────────────────────────────────────────────────────────
    if cluster_col in cluster_df.columns:
        map_df = _add_coords(cluster_df)
        if not map_df.empty:
            map_df["Cluster"] = map_df[cluster_col].astype(str)
            hover_extra = {
                c: True
                for c in disp_cols
                if c not in ("state", cluster_col)
            }
            fig_map = px.scatter_geo(
                map_df, lat="lat", lon="lon",
                color="Cluster",
                hover_name="state",
                hover_data=hover_extra,
                title=f"{method} Cluster Map — Malaysian States",
                size_max=20, opacity=0.88,
            )
            _geo_layout(fig_map, f"{method} Cluster Map — Malaysian States")
            st.plotly_chart(fig_map, use_container_width=True)

    # ── Static figures ───────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        p = os.path.join(FIGURES_DIR, "cluster_elbow_silhouette.png")
        if os.path.exists(p):
            st.image(p, caption="Elbow & Silhouette Curves", use_container_width=True)
    with col_b:
        pca_file = (
            "cluster_pca_kmeans.png" if method == "K-Means"
            else "cluster_pca_hierarchical.png"
        )
        p = os.path.join(FIGURES_DIR, pca_file)
        if os.path.exists(p):
            st.image(p, caption="PCA Scatter", use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        p = os.path.join(FIGURES_DIR, "cluster_dendrogram.png")
        if os.path.exists(p):
            st.image(p, caption="Dendrogram (Hierarchical)", use_container_width=True)
    with col_d:
        p = os.path.join(FIGURES_DIR, "cluster_profiles.png")
        if os.path.exists(p):
            st.image(p, caption="Cluster Feature Profiles", use_container_width=True)

    # ── Elbow metrics table ──────────────────────────────────────────────────
    elbow = clust.get("elbow_metrics", {})
    if elbow:
        st.subheader("Elbow / Silhouette / Davies-Bouldin Metrics")
        k_range = elbow.get("k_range", [])
        if k_range:
            elbw_df = pd.DataFrame({
                "K":              k_range,
                "Inertia":        elbow.get("inertias",   [None] * len(k_range)),
                "Silhouette":     elbow.get("silhouettes",[None] * len(k_range)),
                "Davies-Bouldin": elbow.get("db_scores",  [None] * len(k_range)),
            })
            st.dataframe(elbw_df, use_container_width=True, hide_index=True)
        best_k = clust.get("best_k")
        if best_k:
            st.success(f"Selected K = {best_k}  (best silhouette score)", icon="✅")

    # ── K-Means vs Hierarchical comparison ──────────────────────────────────
    cm_path = os.path.join(MODELS_DIR, "cluster_metrics_summary.csv")
    if os.path.exists(cm_path):
        st.subheader("K-Means vs Hierarchical — Evaluation Metrics")
        st.dataframe(
            pd.read_csv(cm_path),
            use_container_width=True, hide_index=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FUEL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Fuel Prices & CPI Inflation")

    # ── Fuel price trend ─────────────────────────────────────────────────────
    fuel_plot = fuel_df.dropna(subset=["ron95"]).sort_values("date")

    fig_fuel = go.Figure()
    for col, label, color in [
        ("ron95",    "RON 95",  "#2563eb"),
        ("ron97",    "RON 97",  "#16a34a"),
        ("diesel",   "Diesel",  "#d97706"),
        ("avg_fuel", "Average", "#7c3aed"),
    ]:
        if col in fuel_plot.columns:
            fig_fuel.add_trace(go.Scatter(
                x=fuel_plot["date"], y=fuel_plot[col],
                mode="lines", name=label,
                line=dict(color=color, width=1.8),
            ))
    fig_fuel.update_layout(
        title="Monthly Fuel Prices (RM/litre)",
        xaxis_title="Date", yaxis_title="Price (RM)",
        height=380, margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_fuel, use_container_width=True)

    # ── Pearson correlation table ─────────────────────────────────────────────
    if fuel_corr:
        st.subheader("Pearson Correlation — Fuel Price vs CPI Inflation")
        corr_rows = [
            {
                "Fuel Type": ftype,
                "Contemporaneous r": vals.get("contemporaneous"),
                "Lag-1 r (fuel leads inflation)": vals.get("lag1"),
            }
            for ftype, vals in fuel_corr["correlations"].items()
        ]
        st.dataframe(pd.DataFrame(corr_rows), use_container_width=True, hide_index=True)
        st.caption(
            f"Based on {fuel_corr['n_overlap_months']} overlapping months "
            f"({fuel_corr['overlap_start']} → {fuel_corr['overlap_end']})"
        )

    st.divider()

    # ── ARIMAX experiment ─────────────────────────────────────────────────────
    exog_exp = arima.get("fuel_exog_experiment", {})
    if exog_exp.get("available"):
        st.subheader("ARIMAX Experiment — Fuel as Exogenous Regressor")
        st.caption(
            "Both models are trained on the same fuel/CPI overlap window and evaluated "
            "on identical held-out test months."
        )
        ex_m = exog_exp.get("arimax_metrics", {})
        ar_m = exog_exp.get("arima_metrics",  {})
        pct  = exog_exp.get("rmse_improvement_pct", 0.0)

        c1, c2, c3 = st.columns(3)
        c1.metric("ARIMAX RMSE",            f"{ex_m['RMSE']:.4f}" if ex_m.get("RMSE") else "—")
        c2.metric("Univariate ARIMA RMSE",  f"{ar_m['RMSE']:.4f}" if ar_m.get("RMSE") else "—")
        c3.metric("RMSE Improvement",       f"{pct:+.2f}%",
                  help="Positive = ARIMAX beats univariate ARIMA; negative = univariate wins")

        coefs = exog_exp.get("exog_coefficients", {})
        if coefs:
            st.subheader("Fuel Price Coefficient (full-window refit)")
            coef_rows = [
                {
                    "Variable":          col,
                    "Coefficient":       vals.get("coef"),
                    "p-value":           vals.get("pvalue"),
                    "Significant (p<0.05)": "Yes" if (vals.get("pvalue") or 1.0) < 0.05 else "No",
                }
                for col, vals in coefs.items()
            ]
            st.dataframe(pd.DataFrame(coef_rows), use_container_width=True, hide_index=True)

        n   = exog_exp.get("n_overlap_months", "?")
        ord_ = tuple(exog_exp.get("order", []))
        st.caption(
            f"ARIMAX order {ord_} · test horizon {exog_exp.get('test_months')} months · "
            f"{n} overlapping months used."
        )

    elif exog_exp:
        st.info(f"ARIMAX experiment not available: {exog_exp.get('reason', 'unknown reason')}")
    else:
        st.info("ARIMAX experiment data not found — re-run the pipeline.")
