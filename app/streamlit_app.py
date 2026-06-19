"""
Streamlit dashboard — Theme 3: Smart Government — Malaysian Cost of Living AI.
Tabs: Overview | Time Series Forecast | State Clustering | Fuel Analysis
"""
import os
import sys
import json
import html as _html
import base64
import urllib.request
import subprocess

import streamlit.components.v1 as components

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
  justify-content: center !important;
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

/* ── Metric chips (time series) ── */
.metric-row {
  display: flex; gap: 10px; flex-wrap: wrap;
  margin-bottom: 16px; justify-content: center;
}
.metric-chip {
  background: #f4f6fa; border: 1px solid #d1d5db;
  border-radius: 6px; padding: 6px 14px; font-size: 0.82rem;
}
.metric-chip strong { color: #1a3c6e; }

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

/* ── HTML app-table (Evaluation Metrics, Fuel Coefficients, etc.) ── */
.app-table {
  width: 100%; border-collapse: collapse;
  font-size: 0.85rem; font-family: 'Segoe UI', system-ui, sans-serif;
}
.app-table th {
  background: #1a3c6e; color: #ffffff;
  padding: 9px 14px; text-align: left; font-weight: 600; font-size: 0.83rem;
}
.app-table td {
  padding: 8px 14px; border-bottom: 1px solid #d1d5db; color: #1e2330;
}
.app-table tr:nth-child(even) td { background: #f9fafb; }
.app-table tr:hover td { background: #f0f4ff; }

/* ── Radio / select controls ── */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] [role="radiogroup"] label,
[data-testid="stRadio"] [role="radiogroup"] label p,
[data-testid="stRadio"] [role="radiogroup"] label span,
[data-testid="stRadio"] div p,
[data-testid="stRadio"] > div > div { color: #1e2330 !important; }

/* ── Border containers → HTML card style ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #ffffff !important;
  border-radius: 10px !important;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08) !important;
  border: none !important;
  padding: 20px 24px 24px 24px !important;
  margin-bottom: 22px !important;
}

/* ── Slider label ── */
[data-testid="stSlider"] label { color: #1e2330 !important; }

/* ── Selectbox + Multiselect — full light theme ── */
[data-testid="stMultiSelect"] label,
[data-testid="stSelectbox"] label { color: #1e2330 !important; }

/* Selectbox trigger box */
[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] > div > div > div {
  background-color: #ffffff !important;
  border-color: #d1d5db !important;
  color: #1e2330 !important;
}
/* Combobox input text */
[data-testid="stSelectbox"] input[role="combobox"],
[data-testid="stSelectbox"] input {
  background-color: #ffffff !important;
  color: #1e2330 !important;
}
/* The displayed selected value text */
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [class*="ValueContainer"] div,
[data-testid="stSelectbox"] [class*="singleValue"] {
  background-color: #ffffff !important;
  color: #1e2330 !important;
}
/* Dropdown arrow icon */
[data-testid="stSelectbox"] svg { fill: #6b7280 !important; }

/* Dropdown listbox popup */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"] {
  background-color: #ffffff !important;
  border: 1px solid #d1d5db !important;
  border-radius: 6px !important;
}
/* Individual options */
[role="option"] {
  background-color: #ffffff !important;
  color: #1e2330 !important;
}
[role="option"]:hover,
[role="option"][aria-selected="true"] {
  background-color: #f4f6fa !important;
  color: #1a3c6e !important;
}

/* Multiselect tags */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
  background-color: #1a3c6e !important;
  color: #ffffff !important;
}
[data-testid="stMultiSelect"] > div > div {
  background-color: #ffffff !important;
  border-color: #d1d5db !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] { color: #6b7280 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Malaysia GeoJSON (choropleth maps) ──────────────────────────────────────
_MY_GEOJSON_URL = (
    "https://raw.githubusercontent.com/codeforgermany/"
    "click_that_hood/main/public/data/malaysia.geojson"
)
_MY_NAME_MAP = {
    "Pulau Pinang":      "Penang",
    "W.P. Kuala Lumpur": "Federal Territory of Kuala Lumpur",
    "W.P. Putrajaya":    "Federal Territory of Putrajaya",
    "W.P. Labuan":       "Labuan",
}


@st.cache_data(show_spinner=False)
def load_malaysia_geojson() -> dict | None:
    try:
        with urllib.request.urlopen(_MY_GEOJSON_URL, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


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


# ─── Style constants ─────────────────────────────────────────────────────────
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
_TEXT        = "#1e2330"
_MUTED       = "#6b7280"
_GRID        = "#e5e7eb"
_ZEROLINE    = "#d1d5db"
_FONT_FAMILY = "'Segoe UI', system-ui, sans-serif"

_AXIS_STYLE = dict(
    title_font=dict(color=_TEXT, size=12, family=_FONT_FAMILY),
    tickfont=dict(color=_TEXT, size=11, family=_FONT_FAMILY),
    gridcolor=_GRID,
    zerolinecolor=_ZEROLINE,
    linecolor=_ZEROLINE,
)

_DENDRO_COLORS = {
    "b": "#1a3c6e", "g": "#22c55e", "r": "#e8523a",
    "c": "#06b6d4", "m": "#a855f7", "y": "#f59e0b", "k": "#374151",
}


def _style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font=dict(family=_FONT_FAMILY, color=_TEXT, size=12),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        legend=dict(font=dict(color=_TEXT, size=11, family=_FONT_FAMILY)),
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    return fig


def _dendro_color(c: str) -> str:
    if c in _DENDRO_COLORS:
        return _DENDRO_COLORS[c]
    import re
    m = re.match(r"^C(\d+)$", c or "")
    if m:
        return _PALETTE[int(m.group(1)) % len(_PALETTE)]
    return "#1a3c6e"


# ─── Cluster feature definitions ─────────────────────────────────────────────
_FEATURE_OPTS = {
    "Mean Household Income":   "income_mean_latest",
    "Median Household Income": "income_median_latest",
    "Mean CPI Index":          "mean_cpi_index",
    "CPI Growth Rate":         "cpi_growth_rate",
    "CPI Volatility":          "cpi_volatility",
}
_FEATURE_LABELS = {v: k for k, v in _FEATURE_OPTS.items()}
_PROFILE_FEATS  = [
    ("mean_cpi_index",       "Mean CPI"),
    ("cpi_growth_rate",      "CPI Growth %"),
    ("cpi_volatility",       "CPI Volatility"),
    ("income_mean_latest",   "Mean Income"),
    ("income_median_latest", "Median Income"),
]


# ─── Chart helpers ────────────────────────────────────────────────────────────
def _make_cluster_scatter(df: pd.DataFrame, x_col: str, y_col: str) -> go.Figure:
    labels = sorted(df["cluster_label"].unique())
    fig = go.Figure()
    for i, lbl in enumerate(labels):
        pts = df[df["cluster_label"] == lbl]
        fig.add_trace(go.Scatter(
            x=pts[x_col], y=pts[y_col],
            mode="markers+text",
            name=lbl,
            text=pts["state"],
            textposition="top center",
            textfont=dict(size=10),
            marker=dict(size=14, color=_PALETTE[i % len(_PALETTE)], opacity=0.85),
        ))
    fig.update_layout(
        title=dict(
            text=f"State Clusters: {_FEATURE_LABELS[x_col]} vs {_FEATURE_LABELS[y_col]}",
            font=dict(size=13, color=_TEXT, family=_FONT_FAMILY),
        ),
        xaxis_title=_FEATURE_LABELS[x_col],
        yaxis_title=_FEATURE_LABELS[y_col],
        height=480, margin=dict(l=0, r=0, t=48, b=80),
        legend=dict(orientation="h", y=-0.22),
        hovermode="closest",
    )
    return _style(fig)


def _make_pca_scatter(df: pd.DataFrame, title: str, pca_var: list) -> go.Figure:
    if "pc1" not in df.columns or df["pc1"].isna().all():
        return None
    labels = sorted(df["cluster_label"].unique())
    vx = f" ({pca_var[0]*100:.1f}% var)" if len(pca_var) > 0 else ""
    vy = f" ({pca_var[1]*100:.1f}% var)" if len(pca_var) > 1 else ""
    fig = go.Figure()
    for i, lbl in enumerate(labels):
        pts = df[df["cluster_label"] == lbl]
        fig.add_trace(go.Scatter(
            x=pts["pc1"], y=pts["pc2"],
            mode="markers+text", name=lbl,
            text=pts["state"], textposition="top center",
            textfont=dict(size=9),
            marker=dict(size=14, color=_PALETTE[i % len(_PALETTE)], opacity=0.85,
                        line=dict(color="#fff", width=1)),
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=_TEXT, family=_FONT_FAMILY)),
        xaxis_title="PC1" + vx, yaxis_title="PC2" + vy,
        height=380, margin=dict(l=0, r=0, t=48, b=70),
        legend=dict(orientation="h", y=-0.25),
    )
    return _style(fig)


def _make_elbow_chart(elbow: dict, best_k: int | None) -> go.Figure:
    k  = elbow.get("k_range", [])
    si = elbow.get("silhouettes", [])
    db = elbow.get("db_scores", [])
    w  = elbow.get("inertias", [])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name="Silhouette (↑ better)", x=k, y=si, yaxis="y",
        mode="lines+markers", line=dict(color="#22c55e", width=2), marker=dict(size=7),
    ))
    fig.add_trace(go.Scatter(
        name="Davies-Bouldin (↓ better)", x=k, y=db, yaxis="y",
        mode="lines+markers", line=dict(color="#e8523a", width=2), marker=dict(size=7),
    ))
    fig.add_trace(go.Scatter(
        name="Inertia / WCSS (elbow)", x=k, y=w, yaxis="y2",
        mode="lines+markers", line=dict(color="#1a3c6e", width=2, dash="dot"), marker=dict(size=7),
    ))
    shapes = []
    annotations = []
    if best_k:
        shapes.append(dict(type="line", x0=best_k, x1=best_k, yref="paper", y0=0, y1=1,
                           line=dict(color="#9ca3af", dash="dot", width=1.5)))
        annotations.append(dict(x=best_k, y=1, yref="paper", xanchor="left",
                                text=f"best k={best_k}", showarrow=False,
                                font=dict(size=10, color="#6b7280")))
    fig.update_layout(
        title=dict(text="Optimal k Selection", font=dict(size=13, color=_TEXT)),
        xaxis=dict(title="Number of clusters (k)", dtick=1),
        yaxis=dict(title="Silhouette / Davies-Bouldin"),
        yaxis2=dict(title="Inertia (WCSS)", overlaying="y", side="right", showgrid=False),
        shapes=shapes, annotations=annotations,
        legend=dict(orientation="h", y=-0.25),
        height=380, margin=dict(l=0, r=55, t=48, b=70),
    )
    return _style(fig)


def _make_profiles_heatmap(df: pd.DataFrame) -> go.Figure:
    labels = sorted(df["cluster_label"].unique())
    feat_keys = [f[0] for f in _PROFILE_FEATS]
    feat_lbls = [f[1] for f in _PROFILE_FEATS]
    raw = [[df.loc[df["cluster_label"] == lbl, k].mean() for k in feat_keys] for lbl in labels]
    z   = [row[:] for row in raw]
    for c in range(len(feat_keys)):
        col = [raw[r][c] for r in range(len(labels))]
        mn, mx = min(col), max(col)
        for r in range(len(labels)):
            z[r][c] = (raw[r][c] - mn) / (mx - mn) if mx != mn else 0.5
    annot = [[f"{v:.0f}" if v >= 1000 else f"{v:.2f}" for v in row] for row in raw]
    fig = go.Figure(go.Heatmap(
        x=feat_lbls, y=labels, z=z,
        text=annot, texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale="RdYlGn", showscale=True,
        colorbar=dict(title="Relative", thickness=14),
        hovertemplate="%{y}<br>%{x}: %{text}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Feature Averages per Cluster (colour = relative)", font=dict(size=12, color=_TEXT)),
        height=380, margin=dict(t=44, r=20, b=70, l=150),
        xaxis=dict(tickangle=-20),
    )
    return _style(fig)


def _make_dendrogram(dendro: dict) -> go.Figure:
    ic     = dendro.get("icoord", [])
    dc     = dendro.get("dcoord", [])
    ivl    = dendro.get("ivl", [])
    colors = dendro.get("color_list", [])
    traces = []
    for i, (xs, ys) in enumerate(zip(ic, dc)):
        c   = colors[i] if i < len(colors) else "b"
        traces.append(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color=_dendro_color(c), width=1.8),
            hovertemplate=f"Merge distance: {max(ys):.2f}<extra></extra>",
            showlegend=False,
        ))
    tickvals = [10 * i + 5 for i in range(len(ivl))]
    fig = go.Figure(traces)
    fig.update_layout(
        title=dict(text="Ward-linkage dendrogram — states merge bottom-up by similarity",
                   font=dict(size=12, color=_TEXT)),
        xaxis=dict(tickvals=tickvals, ticktext=ivl, tickangle=-40,
                   title="State", automargin=True),
        yaxis=dict(title="Distance (Ward)", zeroline=False),
        height=420, margin=dict(t=44, r=20, b=90, l=20),
        hovermode="closest",
    )
    return _style(fig)


def _make_choropleth_cpi(geojson: dict, df: pd.DataFrame) -> go.Figure:
    locations, z_vals, hover = [], [], []
    for _, row in df.iterrows():
        geo_name = _MY_NAME_MAP.get(row["state"], row["state"])
        locations.append(geo_name)
        z_vals.append(row["mean_cpi"])
        hover.append(
            f"<b>{row['state']}</b><br>"
            f"Mean CPI Index: {row['mean_cpi']:.1f}"
        )
    fig = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.name",
        locations=locations, z=z_vals, text=hover, hoverinfo="text",
        colorscale="YlOrRd",
        colorbar=dict(title=dict(text="CPI Index", side="right"), thickness=14, len=0.6),
        marker=dict(line=dict(color="#fff", width=0.8)),
    ))
    fig.update_geos(fitbounds="locations", visible=False,
                    showland=True, landcolor="#f1f5f9",
                    showocean=True, oceancolor="#e0f2fe",
                    showcoastlines=True, coastlinecolor="#94a3b8")
    fig.update_layout(
        height=420, margin=dict(t=0, b=0, l=0, r=60),
        paper_bgcolor="#ffffff",
        font=dict(family=_FONT_FAMILY, color=_TEXT, size=12),
    )
    return fig


def _make_choropleth_cluster(geojson: dict, df: pd.DataFrame) -> go.Figure:
    labels = sorted(df["cluster_label"].unique())
    n      = len(labels)
    idx    = {lbl: i for i, lbl in enumerate(labels)}
    colorscale = []
    for i, _ in enumerate(labels):
        c = _PALETTE[i % len(_PALETTE)]
        colorscale += [[i / n, c], [(i + 1) / n, c]]
    locations, z_vals, hover = [], [], []
    for _, row in df.iterrows():
        geo_name = _MY_NAME_MAP.get(row["state"], row["state"])
        locations.append(geo_name)
        z_vals.append(idx[row["cluster_label"]])
        hover.append(
            f"<b>{row['state']}</b><br>"
            f"Cluster: {row['cluster_label']}<br>"
            f"Mean Income: RM {int(row['income_mean_latest']):,}<br>"
            f"CPI Growth: {row['cpi_growth_rate']:.2f}%"
        )
    fig = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.name",
        locations=locations, z=z_vals, text=hover, hoverinfo="text",
        colorscale=colorscale, zmin=-0.5, zmax=n - 0.5,
        colorbar=dict(
            title=dict(text="Cluster", side="right"),
            thickness=14, len=0.6,
            tickvals=list(range(n)),
            ticktext=labels, nticks=n,
        ),
        marker=dict(line=dict(color="#fff", width=0.8)),
    ))
    fig.update_geos(fitbounds="locations", visible=False,
                    showland=True, landcolor="#f1f5f9",
                    showocean=True, oceancolor="#e0f2fe",
                    showcoastlines=True, coastlinecolor="#94a3b8")
    fig.update_layout(
        height=440, margin=dict(t=0, b=0, l=0, r=140),
        paper_bgcolor="#ffffff",
        font=dict(family=_FONT_FAMILY, color=_TEXT, size=12),
    )
    return fig


# ─── Interactive image (hover zoom + click lightbox) ────────────────────────
def _interactive_image(path: str, alt: str = "") -> None:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    uid = abs(hash(path)) % 10 ** 9
    st.markdown(f"""
<style>
#img-wrap-{uid} {{
    position: relative; width: 100%; cursor: zoom-in;
    border-radius: 6px; overflow: hidden;
}}
#img-wrap-{uid} img {{
    width: 100%; display: block; border-radius: 6px;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}}
#img-wrap-{uid}:hover img {{
    transform: scale(1.015);
    box-shadow: 0 6px 28px rgba(0,0,0,0.22);
}}
#img-wrap-{uid}::after {{
    content: "🔍 Click to expand";
    position: absolute; bottom: 12px; right: 14px;
    background: rgba(26,60,110,0.82); color: #fff;
    font-size: 0.78rem; padding: 4px 10px; border-radius: 4px;
    opacity: 0; transition: opacity 0.2s; pointer-events: none;
}}
#img-wrap-{uid}:hover::after {{ opacity: 1; }}
#overlay-{uid} {{
    display: none; position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: rgba(0,0,0,0.88); z-index: 99999;
    cursor: zoom-out; align-items: center; justify-content: center;
}}
#overlay-{uid}.open {{ display: flex; }}
#overlay-{uid} img {{
    max-width: 92vw; max-height: 92vh;
    border-radius: 8px; box-shadow: 0 12px 60px rgba(0,0,0,0.5);
}}
#overlay-close-{uid} {{
    position: fixed; top: 16px; right: 20px;
    color: #fff; font-size: 1.8rem; cursor: pointer;
    z-index: 100000; line-height: 1; user-select: none;
}}
</style>
<div id="img-wrap-{uid}"
     onclick="document.getElementById('overlay-{uid}').classList.add('open')">
  <img src="data:image/png;base64,{b64}" alt="{alt}" />
</div>
<div id="overlay-{uid}" onclick="this.classList.remove('open')">
  <span id="overlay-close-{uid}"
        onclick="event.stopPropagation();document.getElementById('overlay-{uid}').classList.remove('open')">✕</span>
  <img src="data:image/png;base64,{b64}" alt="{alt}" />
</div>
""", unsafe_allow_html=True)


# ─── HTML table helper ───────────────────────────────────────────────────────
def _html_table(df: pd.DataFrame) -> None:
    headers = "".join(f"<th>{_html.escape(str(c))}</th>" for c in df.columns)
    rows = ""
    for _, row in df.iterrows():
        cells = "".join(
            f"<td>{_html.escape('' if pd.isna(v) else str(v))}</td>" for v in row
        )
        rows += f"<tr>{cells}</tr>"
    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table class="app-table">'
        f'<thead><tr>{headers}</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )


# ─── Pipeline runner ─────────────────────────────────────────────────────────
def _run_pipeline() -> None:
    script = os.path.join(ROOT_DIR, "run_pipeline.py")
    lines: list[str] = []

    _, mid, _ = st.columns([1, 4, 1])
    with mid:
        with st.status("Running Analysis Pipeline…", expanded=True) as status:
            log_slot = st.empty()
            proc = subprocess.Popen(
                [sys.executable, "-u", script, "--no-dashboard"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=ROOT_DIR,
            )
            for raw in proc.stdout:
                lines.append(raw.rstrip())
                escaped = _html.escape("\n".join(lines[-25:]))
                log_slot.markdown(
                    f'<div style="background:#0f172a;color:#94a3b8;'
                    f'font-family:monospace;font-size:0.82rem;line-height:1.55;'
                    f'height:260px;overflow-y:auto;overflow-x:hidden;'
                    f'border-radius:8px;padding:14px 16px;'
                    f'white-space:pre-wrap;word-break:break-word;'
                    f'box-shadow:inset 0 2px 6px rgba(0,0,0,0.3);">'
                    f'{escaped}</div>',
                    unsafe_allow_html=True,
                )
            proc.wait()
            if proc.returncode == 0:
                status.update(label="✅ Pipeline complete!", state="complete")
            else:
                status.update(
                    label=f"❌ Pipeline failed (exit code {proc.returncode})",
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

# ─── Pipeline status + Run button ────────────────────────────────────────────
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
    _do_run = st.button("▶  Run Analysis Pipeline", type="primary", use_container_width=True)

# Call outside column so the log panel spans full page width
if _do_run:
    _run_pipeline()

if not ready:
    st.stop()

# ─── Load data ───────────────────────────────────────────────────────────────
arima     = load_arima()
clust     = load_clustering()
fuel_corr = load_fuel_correlation()
overall   = load_df("overall_inflation.csv")
cpi_div   = load_df("cpi_inflation_clean.csv")
fuel_df   = load_df("fuelprice_clean.csv")
kmeans_df = load_df("states_kmeans_clustered.csv")
hier_df   = load_df("states_hierarchical_clustered.csv")

overall["date"] = pd.to_datetime(overall["date"])
cpi_div["date"] = pd.to_datetime(cpi_div["date"])
fuel_df["date"] = pd.to_datetime(fuel_df["date"])

cpi_state = load_df("cpi_state_clean.csv")
cpi_state["date"] = pd.to_datetime(cpi_state["date"])
all_states = sorted(cpi_state["state"].unique().tolist())

# ─── Tabs ────────────────────────────────────────────────────────────────────
_active_tab = max(0, min(3, int(st.query_params.get("tab", "0"))))

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Time Series Forecast",
    "State Clustering",
    "Fuel Analysis",
])

# Persist active tab in URL so page refresh restores it.
# components.html re-runs on every Streamlit render, so listeners stay fresh.
components.html(f"""
<script>
(function(){{
  var T = {_active_tab};
  function setup() {{
    var btns = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
    if (!btns.length) {{ setTimeout(setup, 60); return; }}
    if (btns[T] && btns[T].getAttribute('aria-selected') !== 'true') btns[T].click();
    btns.forEach(function(b, i) {{
      if (b._ql) return;
      b._ql = true;
      b.addEventListener('click', function() {{
        var u = new URL(window.parent.location.href);
        u.searchParams.set('tab', i);
        window.parent.history.replaceState(null, '', u);
      }});
    }});
  }}
  setTimeout(setup, 150);
}})();
</script>
""", height=0)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Project summary ──────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">Project Summary</p>
        <p class="card-desc">
          This system analyses Malaysia's Consumer Price Index (CPI) inflation across
          13 divisions and 16 states, applying <strong>ARIMA time series forecasting</strong>
          on the national inflation trend and <strong>K-Means clustering</strong> to group
          states by their CPI and income profile. Fuel price dynamics and their correlation
          with inflation are also examined. Data sourced from the Department of Statistics
          Malaysia (DOSM) open data portal.
        </p>
        """, unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("States covered",         "16")
        c2.metric("CPI divisions tracked",  "13")
        c3.metric("State CPI data from",    "2010–")
        c4.metric("Fuel price data from",   "2017–")

    # ── National CPI Inflation — dual-axis (YoY line + MoM bars) ────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">National CPI Inflation — Last 5 Years</p>
        <p class="card-desc">
          Year-on-year (YoY) national CPI inflation shown as a line;
          month-on-month (MoM) changes as bars. Green bars indicate deflation months.
        </p>
        """, unsafe_allow_html=True)

        cutoff5 = overall["date"].max() - pd.DateOffset(years=5)
        r5 = overall[overall["date"] >= cutoff5].sort_values("date")
        mom_colors = ["#22c55e" if v < 0 else "#e8523a" for v in r5["inflation_mom"].fillna(0)]

        fig_nat = go.Figure()
        fig_nat.add_trace(go.Scatter(
            x=r5["date"], y=r5["inflation_yoy"],
            mode="lines", name="YoY Inflation (%)",
            line=dict(color="#1a3c6e", width=2.5),
        ))
        fig_nat.add_trace(go.Bar(
            x=r5["date"], y=r5["inflation_mom"],
            name="MoM Inflation (%)", yaxis="y2",
            marker=dict(color=mom_colors, opacity=0.6),
        ))
        fig_nat.add_hline(y=0, line_dash="dot", line_color="#9ca3af", line_width=1)
        fig_nat.update_layout(
            xaxis=dict(title="Date", tickformat="%b %Y"),
            yaxis=dict(title="YoY Inflation (%)"),
            yaxis2=dict(title="MoM Inflation (%)", overlaying="y", side="right",
                        showgrid=False, zeroline=False),
            height=380, margin=dict(l=0, r=64, t=10, b=0),
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.22),
        )
        _style(fig_nat)
        st.plotly_chart(fig_nat, use_container_width=True)

    # ── CPI Inflation by Division — Last 3 Years ─────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">CPI Inflation by Division — Last 3 Years</p>
        <p class="card-desc">
          Year-on-year inflation trends broken down by all 13 DOSM CPI divisions.
          Divisions cover food, housing, transport, health, education, and more.
        </p>
        """, unsafe_allow_html=True)

        cutoff3  = cpi_div["date"].max() - pd.DateOffset(years=3)
        div_rec  = cpi_div[cpi_div["date"] >= cutoff3].dropna(subset=["inflation_yoy"])
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
            legend=dict(font_size=10, x=1.01, y=1),
            hovermode="x unified",
        )
        _style(fig_div)
        st.plotly_chart(fig_div, use_container_width=True)

    # ── Division Inflation Heatmap (static eval figure) ──────────────────────
    _div_hm_path = os.path.join(FIGURES_DIR, "eval_division_heatmap.png")
    if os.path.exists(_div_hm_path):
        with st.container(border=True):
            st.markdown("""
            <p class="card-title">Division Inflation Heatmap</p>
            <p class="card-desc">
              Mean annual year-on-year inflation per CPI division and year.
              Darker red cells indicate higher inflation; blue/green cells indicate lower or negative growth.
            </p>
            """, unsafe_allow_html=True)
            _interactive_image(_div_hm_path, "Division Inflation Heatmap")

    # ── State CPI Index Explorer (single state dropdown) ──────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">State CPI Index Explorer</p>
        <p class="card-desc">
          Monthly overall CPI index for a selected state (2010–present).
          Base year: 2010 = 100. A rising index indicates cumulative price growth.
        </p>
        """, unsafe_allow_html=True)

        sel_state = st.selectbox("State", all_states, key="ov_state_sel")
        grp_st = cpi_state[
            (cpi_state["state"] == sel_state) & (cpi_state["division"] == "overall")
        ].sort_values("date")
        if not grp_st.empty:
            fig_st = go.Figure()
            fig_st.add_trace(go.Scatter(
                x=grp_st["date"], y=grp_st["index"],
                mode="lines", name=sel_state,
                line=dict(color="#1a3c6e", width=2),
                fill="tozeroy", fillcolor="rgba(26,60,110,0.07)",
            ))
            fig_st.update_layout(
                title=dict(text=f"CPI Index — {sel_state}",
                           font=dict(size=13, color=_TEXT, family=_FONT_FAMILY)),
                xaxis=dict(title="Date", tickformat="%b %Y"),
                yaxis_title="CPI Index (Base 2010 = 100)",
                height=340, margin=dict(l=0, r=20, t=40, b=0),
                hovermode="x unified", showlegend=False,
            )
            _style(fig_st)
            st.plotly_chart(fig_st, use_container_width=True)

    # ── State CPI Index Map (choropleth — mean CPI per state) ─────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">State CPI Index Map</p>
        <p class="card-desc">
          Mean CPI index per state (2010–present, base year 2010 = 100).
          Darker shading indicates higher accumulated price levels.
          Hover over a state for details.
        </p>
        """, unsafe_allow_html=True)

        mean_cpi_df = (
            cpi_state[cpi_state["division"] == "overall"]
            .groupby("state", as_index=False)["index"]
            .mean()
            .rename(columns={"index": "mean_cpi"})
        )
        geojson = load_malaysia_geojson()
        if geojson is not None and not mean_cpi_df.empty:
            fig_cpi_map = _make_choropleth_cpi(geojson, mean_cpi_df)
            st.plotly_chart(fig_cpi_map, use_container_width=True)
        else:
            st.info("Map unavailable — GeoJSON could not be loaded.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TIME SERIES FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    order = arima.get("arima_order", ["?", "?", "?"])
    m     = arima.get("metrics", {})
    s     = arima.get("stationarity", {})

    # ── ARIMA Forecast card ───────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">ARIMA National Inflation Forecast</p>
        <p class="card-desc">
          ARIMA fitted on monthly national CPI year-on-year inflation (overall division, 1981–present).
          Order selected via BIC grid search; stationarity verified with the Augmented Dickey-Fuller test.
          The model is evaluated on a held-out 24-month test window before forecasting.
        </p>
        """, unsafe_allow_html=True)

        # Horizon slider + run button
        col_sl, col_rb = st.columns([4, 1])
        with col_sl:
            horizon = st.slider("Forecast horizon (months)", 1, 48, 48, key="ts_horizon")
        with col_rb:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            run_live = st.button("↺ Run Forecast", type="primary",
                                 use_container_width=True, key="ts_run")

        # Metric chips
        stat_txt = "✅ Yes" if s.get("is_stationary") else "⚠ No"
        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-chip">MAE <strong>{m.get("MAE", "—")}</strong></div>
          <div class="metric-chip">RMSE <strong>{m.get("RMSE", "—")}</strong></div>
          <div class="metric-chip">sMAPE <strong>{"—" if m.get("sMAPE") is None else str(m["sMAPE"]) + "%"}</strong></div>
          <div class="metric-chip">MASE <strong>{m.get("MASE", "—")}</strong></div>
          <div class="metric-chip">AIC <strong>{arima.get("aic", "—")}</strong></div>
          <div class="metric-chip">BIC <strong>{arima.get("bic", "—")}</strong></div>
          <div class="metric-chip">ADF p-value <strong>{s.get("p_value", "—")}</strong></div>
          <div class="metric-chip">Stationary <strong>{stat_txt}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        # Build forecast figure (precomputed or live)
        arima_src = arima
        if run_live:
            with st.spinner("Computing forecast…"):
                from src.time_series import run_live as _run_live
                inf_df = load_df("overall_inflation.csv").copy()
                inf_df["date"] = pd.to_datetime(inf_df["date"])
                precomp_order = tuple(int(x) for x in order) if order else None
                for event in _run_live(inf_df, horizon=horizon,
                                       order=precomp_order, precomputed=arima):
                    if event.get("type") == "result":
                        # run_live wraps result under event["data"]
                        arima_src = event.get("data", event)
                        break

        if "train" not in arima_src:
            st.warning("Forecast data unavailable — re-run the pipeline.")
            st.stop()
        train_dates = pd.to_datetime(arima_src["train"]["dates"])
        train_vals  = np.array(arima_src["train"]["values"])
        cut10       = train_dates.max() - pd.DateOffset(years=10)
        mask10      = train_dates >= cut10
        test_dates  = pd.to_datetime(arima_src["test"]["dates"])
        fc_dates    = pd.to_datetime(arima_src["forecast"]["dates"])
        fc_lower    = list(arima_src["forecast"]["lower"])
        fc_upper    = list(arima_src["forecast"]["upper"])
        fc_dates_l  = list(fc_dates)

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=train_dates[mask10], y=train_vals[mask10],
            mode="lines", name="Historical (train)",
            line=dict(color="#1a3c6e", width=1.5),
        ))
        fig_fc.add_trace(go.Scatter(
            x=test_dates, y=arima_src["test"]["actual"],
            mode="lines+markers", name="Actual (test)",
            marker=dict(size=6, color="#22c55e"),
            line=dict(color="#22c55e", width=2),
        ))
        fig_fc.add_trace(go.Scatter(
            x=test_dates, y=arima_src["test"]["predicted"],
            mode="lines+markers", name="Predicted (test)",
            marker=dict(size=6, color="#ef4444", symbol="diamond"),
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
            x=fc_dates, y=arima_src["forecast"]["values"],
            mode="lines+markers", name=f"Forecast ({len(fc_dates)}m)",
            marker=dict(size=7, symbol="triangle-up", color="#a855f7"),
            line=dict(color="#a855f7", dash="dot", width=2.5),
        ))
        fig_fc.add_hline(y=0, line_dash="dot", line_color="#9ca3af", line_width=0.8)
        if len(test_dates):
            _vline_x = str(test_dates[0].date())
            fig_fc.add_shape(
                type="line", x0=_vline_x, x1=_vline_x, y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(dash="dot", color="#9ca3af", width=1),
            )
            fig_fc.add_annotation(
                x=_vline_x, y=1, xref="x", yref="paper",
                text="test split", showarrow=False,
                xanchor="right", yanchor="top",
                font=dict(size=10, color="#9ca3af"),
            )
        fig_fc.update_layout(
            title=dict(
                text=f"National CPI Inflation Forecast — ARIMA({order[0]},{order[1]},{order[2]})",
                font=dict(color=_TEXT, size=13, family=_FONT_FAMILY),
            ),
            xaxis=dict(title="Date", tickformat="%b %Y"),
            yaxis_title="CPI Inflation YoY (%)",
            height=480, margin=dict(l=0, r=0, t=48, b=0),
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.22),
        )
        _style(fig_fc)
        st.plotly_chart(fig_fc, use_container_width=True)

    # ── Evaluation Metrics table ──────────────────────────────────────────────
    ts_metrics_csv = os.path.join(MODELS_DIR, "ts_metrics_summary.csv")
    if os.path.exists(ts_metrics_csv):
        with st.container(border=True):
            st.markdown("""
            <p class="card-title">Evaluation Metrics</p>
            <p class="card-desc">ARIMA performance on the held-out 24-month test set.</p>
            """, unsafe_allow_html=True)
            _html_table(pd.read_csv(ts_metrics_csv))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CLUSTERING
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    pca_var  = clust.get("pca_variance", [])
    best_k   = clust.get("best_k")
    elbow    = clust.get("elbow_metrics", {})
    dendro   = clust.get("dendrogram", {})

    # ── State Cluster Explorer (interactive scatter — both methods side-by-side) ─
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">State Cluster Explorer</p>
        <p class="card-desc">
          16 Malaysian states clustered by 5 features: mean CPI index, CPI volatility,
          CPI growth rate, latest mean household income, and latest median household income.
          K-Means and Hierarchical (Ward) results shown side-by-side for direct comparison.
        </p>
        """, unsafe_allow_html=True)

        feat_names = list(_FEATURE_OPTS.keys())
        col_x, col_y = st.columns(2)
        with col_x:
            x_sel = st.selectbox("X Axis", feat_names,
                                 index=feat_names.index("Mean Household Income"),
                                 key="cl_x")
        with col_y:
            y_sel = st.selectbox("Y Axis", feat_names,
                                 index=feat_names.index("CPI Growth Rate"),
                                 key="cl_y")

        x_col = _FEATURE_OPTS[x_sel]
        y_col = _FEATURE_OPTS[y_sel]
        col_km, col_hr = st.columns(2)
        with col_km:
            st.markdown('<p class="card-title" style="font-size:13px;margin-bottom:4px">🔵 K-Means</p>',
                        unsafe_allow_html=True)
            st.plotly_chart(_make_cluster_scatter(kmeans_df, x_col, y_col),
                            use_container_width=True)
        with col_hr:
            st.markdown('<p class="card-title" style="font-size:13px;margin-bottom:4px">🟠 Hierarchical (Ward)</p>',
                        unsafe_allow_html=True)
            st.plotly_chart(_make_cluster_scatter(hier_df, x_col, y_col),
                            use_container_width=True)
        st.caption("Each dot is a Malaysian state, coloured by cluster assignment.")

    # ── Malaysia State Cluster Map (choropleth — K-Means) ────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">Malaysia State Cluster Map</p>
        <p class="card-desc">
          Geographic distribution of K-Means cluster assignments across all 16 Malaysian states.
          Each state is coloured by its cluster. Hover for income and CPI details.
          W.P. Labuan (island off Sabah) may not be shown on the map.
        </p>
        """, unsafe_allow_html=True)

        geojson = load_malaysia_geojson()
        if geojson is not None:
            fig_cmap = _make_choropleth_cluster(geojson, kmeans_df)
            st.plotly_chart(fig_cmap, use_container_width=True)
        else:
            st.info("Map unavailable — GeoJSON could not be loaded.")

    # ── Clustering Evaluation Metrics ─────────────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">Clustering Evaluation Metrics</p>
        <p class="card-desc">
          Comparison of K-Means and Hierarchical (Ward linkage) clustering quality.
          Higher Silhouette and Calinski-Harabász are better; lower Davies-Bouldin is better.
        </p>
        """, unsafe_allow_html=True)
        cm_path = os.path.join(MODELS_DIR, "cluster_metrics_summary.csv")
        if os.path.exists(cm_path):
            _html_table(pd.read_csv(cm_path))
        if best_k:
            st.success(f"Selected K = {best_k}  (best silhouette score)", icon="✅")

    # ── Elbow + Silhouette  |  K-Means PCA Projection ────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown('<p class="card-title">Elbow + Silhouette Method</p>',
                        unsafe_allow_html=True)
            if elbow:
                st.plotly_chart(_make_elbow_chart(elbow, best_k), use_container_width=True)
    with col_b:
        with st.container(border=True):
            st.markdown('<p class="card-title">K-Means — PCA Projection</p>',
                        unsafe_allow_html=True)
            fig_pca = _make_pca_scatter(kmeans_df, "K-Means — PCA Projection", pca_var)
            if fig_pca:
                st.plotly_chart(fig_pca, use_container_width=True)

    # ── Hierarchical PCA  |  Cluster Socioeconomic Profiles ──────────────────
    col_c, col_d = st.columns(2)
    with col_c:
        with st.container(border=True):
            st.markdown('<p class="card-title">Hierarchical — PCA Projection</p>',
                        unsafe_allow_html=True)
            fig_hpca = _make_pca_scatter(hier_df, "Hierarchical — PCA Projection", pca_var)
            if fig_hpca:
                st.plotly_chart(fig_hpca, use_container_width=True)
    with col_d:
        with st.container(border=True):
            st.markdown('<p class="card-title">Cluster Socioeconomic Profiles</p>',
                        unsafe_allow_html=True)
            st.plotly_chart(_make_profiles_heatmap(kmeans_df), use_container_width=True)

    # ── State CPI Growth Comparison (static eval figure) ─────────────────────
    _st_cpi_path = os.path.join(FIGURES_DIR, "eval_state_cpi_comparison.png")
    if os.path.exists(_st_cpi_path):
        with st.container(border=True):
            st.markdown("""
            <p class="card-title">State CPI Growth Rate Comparison</p>
            <p class="card-desc">
              Horizontal bar chart ranking all 16 Malaysian states by their overall CPI growth rate.
              States with higher bars have experienced faster cumulative price increases.
            </p>
            """, unsafe_allow_html=True)
            _interactive_image(_st_cpi_path, "State CPI Growth Rate Comparison")

    # ── Hierarchical Clustering — Dendrogram ──────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">Hierarchical Clustering — Dendrogram</p>
        """, unsafe_allow_html=True)
        if dendro:
            st.plotly_chart(_make_dendrogram(dendro), use_container_width=True)
        else:
            p = os.path.join(FIGURES_DIR, "cluster_dendrogram.png")
            if os.path.exists(p):
                st.image(p, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FUEL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:

    # ── Retail Fuel Prices ────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <p class="card-title">Retail Fuel Prices — Monthly Average</p>
        <p class="card-desc">
          Monthly retail prices for RON95, RON97, and Diesel in RM per litre (2017–present).
          Data resampled from weekly pump prices reported by DOSM.
        </p>
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
            xaxis=dict(title="Date", tickformat="%b %Y"),
            yaxis_title="Price (RM / litre)",
            height=380, margin=dict(l=0, r=0, t=10, b=0),
            hovermode="x unified", legend=dict(orientation="h", y=-0.22),
        )
        _style(fig_fuel)
        st.plotly_chart(fig_fuel, use_container_width=True)

    # ── Fuel-Inflation Correlation ────────────────────────────────────────────
    if fuel_corr:
        with st.container(border=True):
            st.markdown("""
            <p class="card-title">Fuel-Inflation Correlation Analysis</p>
            <p class="card-desc">
              Pearson correlation between monthly fuel prices and national CPI YoY inflation.
              <strong>Contemporaneous:</strong> same month.
              <strong>Lag-1:</strong> fuel price leads inflation by one month.
              Values closer to ±1 indicate stronger linear association.
            </p>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-row">
              <div class="metric-chip">Overlap period
                <strong>{fuel_corr.get("overlap_start","—")} → {fuel_corr.get("overlap_end","—")}</strong>
              </div>
              <div class="metric-chip">Months of overlap
                <strong>{fuel_corr.get("n_overlap_months","—")}</strong>
              </div>
            </div>
            """, unsafe_allow_html=True)

            corr    = fuel_corr["correlations"]
            labels  = [k.upper() for k in corr]
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
                title=dict(text="Pearson r — Fuel Prices vs National CPI Inflation",
                           font=dict(color=_TEXT, size=13, family=_FONT_FAMILY)),
                xaxis_title="Fuel Type", yaxis_title="Pearson r",
                yaxis_range=[-1, 1], barmode="group",
                height=360, margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", y=-0.22),
            )
            _style(fig_corr)
            st.plotly_chart(fig_corr, use_container_width=True)

    # ── Fuel-CPI Correlation (static eval figure) ────────────────────────────
    _fuel_corr_path = os.path.join(FIGURES_DIR, "eval_fuel_cpi_correlation.png")
    if os.path.exists(_fuel_corr_path):
        with st.container(border=True):
            st.markdown("""
            <p class="card-title">Fuel Price vs CPI Correlation — Evaluation Chart</p>
            <p class="card-desc">
              Scatter plots of each fuel type against national CPI YoY inflation alongside
              Pearson correlation bars (contemporaneous and lag-1) from the evaluation pipeline.
            </p>
            """, unsafe_allow_html=True)
            _interactive_image(_fuel_corr_path, "Fuel Price vs CPI Correlation")

    # ── ARIMAX vs ARIMA ───────────────────────────────────────────────────────
    exog_exp = arima.get("fuel_exog_experiment", {})
    if exog_exp.get("available"):
        with st.container(border=True):
            st.markdown("""
            <p class="card-title">Does Fuel Improve Inflation Prediction? (ARIMAX vs ARIMA)</p>
            <p class="card-desc">
              Correlation shows association; this tests <strong>predictive value</strong>.
              Two models are fit on the fuel/CPI overlap window and evaluated on the same
              held-out test period: <strong>ARIMAX</strong> (fuel as an exogenous regressor)
              vs a univariate <strong>ARIMA</strong>. A lower RMSE for ARIMAX means fuel adds
              genuine forecasting signal.
            </p>
            """, unsafe_allow_html=True)

            ex_m = exog_exp.get("arimax_metrics", {})
            ar_m = exog_exp.get("arima_metrics",  {})
            pct  = exog_exp.get("rmse_improvement_pct", 0.0)
            coef = (exog_exp.get("exog_coefficients") or {}).get("avg_fuel", {})
            gain_cls = "dc-up" if pct >= 0 else "dc-down"
            st.markdown(f"""
            <div class="metric-row">
              <div class="metric-chip">Overlap
                <strong>{exog_exp.get("overlap_start","—")} → {exog_exp.get("overlap_end","—")}</strong>
              </div>
              <div class="metric-chip">RMSE change from fuel
                <strong class="{gain_cls}">{"+" if pct >= 0 else ""}{pct}%</strong>
              </div>
              <div class="metric-chip">avg_fuel coef
                <strong>{coef.get("coef","—")}</strong> (p={coef.get("pvalue","—")})
              </div>
            </div>
            """, unsafe_allow_html=True)

            fig_exog = go.Figure()
            for name, metrics, color in [
                ("ARIMAX (with fuel)", ex_m, "#1a3c6e"),
                ("ARIMA (univariate)", ar_m, "#e8523a"),
            ]:
                vals = [metrics.get(k) for k in ("RMSE", "MAE", "MASE")]
                fig_exog.add_trace(go.Bar(
                    name=name, x=["RMSE", "MAE", "MASE"], y=vals,
                    marker_color=color,
                    text=[f"{v:.4f}" if v else "" for v in vals],
                    textposition="auto",
                    opacity=0.85 if name.startswith("ARIMA (") else 1.0,
                ))
            fig_exog.update_layout(
                title=dict(text="Test-set error: fuel-augmented vs univariate (lower = better)",
                           font=dict(color=_TEXT, size=12, family=_FONT_FAMILY)),
                yaxis_title="Error", barmode="group",
                height=340, margin=dict(l=0, r=0, t=44, b=0),
                legend=dict(orientation="h", y=-0.22),
            )
            _style(fig_exog)
            st.plotly_chart(fig_exog, use_container_width=True)

            coefs = exog_exp.get("exog_coefficients", {})
            if coefs:
                st.markdown('<p class="card-title" style="margin-top:16px;">'
                            'Fuel Price Coefficient (full-window refit)</p>',
                            unsafe_allow_html=True)
                coef_rows = [
                    {
                        "Variable":             col,
                        "Coefficient":          vals.get("coef"),
                        "p-value":              vals.get("pvalue"),
                        "Significant (p<0.05)": "Yes" if (vals.get("pvalue") or 1.0) < 0.05 else "No",
                    }
                    for col, vals in coefs.items()
                ]
                _html_table(pd.DataFrame(coef_rows))
            st.caption(
                f"ARIMAX order {tuple(exog_exp.get('order', []))} · "
                f"test horizon {exog_exp.get('test_months')} months · "
                f"{exog_exp.get('n_overlap_months','?')} overlapping months used."
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
