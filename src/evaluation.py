"""
Evaluation module.
Produces summary metrics tables and multi-panel comparison figures
for both the time series (ARIMA) and clustering analyses.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "figures")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "models")


# ─── Time Series Evaluation ───────────────────────────────────────────────────

def ts_metrics_table(arima_results: dict) -> pd.DataFrame:
    rows = []
    for state, res in arima_results.items():
        if "error" in res:
            continue
        rows.append({
            "State": state,
            "MAE": res["metrics"]["MAE"],
            "RMSE": res["metrics"]["RMSE"],
            "MAPE (%)": res["metrics"]["MAPE"],
            "Stationary (train)": res["stationarity"]["is_stationary"],
            "Forecast 2030": round(res["forecast_gini"][-1], 4),
        })
    df = pd.DataFrame(rows).sort_values("RMSE")
    df.to_csv(os.path.join(MODELS_DIR, "ts_metrics_summary.csv"), index=False)
    return df


def plot_ts_metrics_comparison(metrics_df: pd.DataFrame, save_path: str = None):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("ARIMA Forecast Evaluation — All States", fontsize=13, fontweight="bold")
    colors = sns.color_palette("muted", len(metrics_df))

    for ax, col, title in zip(
        axes,
        ["MAE", "RMSE", "MAPE (%)"],
        ["Mean Absolute Error", "Root Mean Squared Error", "MAPE (%)"],
    ):
        ax.barh(metrics_df["State"], metrics_df[col], color=colors)
        avg = metrics_df[col].mean()
        ax.axvline(x=avg, color="red", linestyle="--", linewidth=1.2, label=f"Mean={avg:.4f}")
        ax.set_title(title)
        ax.set_xlabel(col)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_gini_trends_all_states(gini_df: pd.DataFrame, save_path: str = None):
    """Line chart of historical Gini for every state (1974–2022)."""
    states = gini_df["state"].unique()
    fig, ax = plt.subplots(figsize=(13, 7))
    palette = sns.color_palette("tab20", len(states))
    for i, state in enumerate(sorted(states)):
        grp = gini_df[gini_df["state"] == state].sort_values("year")
        ax.plot(grp["year"], grp["gini"], marker="o", markersize=3,
                linewidth=1.4, label=state, color=palette[i])
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Gini Coefficient", fontsize=11)
    ax.set_title("Gini Coefficient Trends by State (1974–2022)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=7, ncol=3, loc="upper right")
    ax.axhline(y=0.4, color="black", linestyle=":", linewidth=1, alpha=0.6, label="0.40 threshold")
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


# ─── Clustering Evaluation ────────────────────────────────────────────────────

def cluster_metrics_table(clustering_results: dict) -> pd.DataFrame:
    rows = []
    for method in ("kmeans", "hierarchical"):
        scores = clustering_results[method]["scores"]
        rows.append({
            "Method": method.capitalize(),
            "K": scores["k"],
            "Silhouette": scores["silhouette"],
            "Davies-Bouldin": scores["davies_bouldin"],
            "Calinski-Harabasz": scores["calinski_harabasz"],
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(MODELS_DIR, "cluster_metrics_summary.csv"), index=False)
    return df


def plot_poverty_cluster_boxplot(df_clustered: pd.DataFrame, save_path: str = None):
    """Box plot of poverty rate across cluster labels."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Poverty & Income Distribution by Cluster", fontsize=13, fontweight="bold")

    order = sorted(df_clustered["cluster_label"].unique())
    sns.boxplot(data=df_clustered, x="cluster_label", y="poverty",
                order=order, palette="Set2", ax=axes[0])
    axes[0].set_title("Poverty Rate by Cluster")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Poverty Rate (%)")
    axes[0].tick_params(axis="x", rotation=20)

    sns.boxplot(data=df_clustered, x="cluster_label", y="income_mean",
                order=order, palette="Set3", ax=axes[1])
    axes[1].set_title("Mean Income by Cluster")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Mean Income (RM)")
    axes[1].tick_params(axis="x", rotation=20)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_poverty_change_heatmap(poverty_wide: pd.DataFrame, save_path: str = None):
    """Heatmap of absolute poverty change 2019->2022 by state."""
    pivot = poverty_wide.groupby("state")["poverty_abs_change"].mean().reset_index()
    pivot = pivot.sort_values("poverty_abs_change", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#2166ac" if v < 0 else "#d73027" for v in pivot["poverty_abs_change"]]
    ax.barh(pivot["state"], pivot["poverty_abs_change"], color=colors)
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.set_xlabel("Change in Absolute Poverty Rate (percentage points)")
    ax.set_title("Average Absolute Poverty Change by State (2019->2022)", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_income_vs_gini_scatter(df_district: pd.DataFrame, save_path: str = None):
    """Scatter of mean income vs Gini coloured by state."""
    fig, ax = plt.subplots(figsize=(10, 6))
    states = df_district["state"].unique()
    palette = sns.color_palette("tab20", len(states))
    for i, state in enumerate(sorted(states)):
        grp = df_district[df_district["state"] == state]
        ax.scatter(grp["income_mean"], grp["gini"], label=state,
                   color=palette[i], s=55, alpha=0.75, edgecolors="white", linewidths=0.4)
    ax.set_xlabel("Mean Household Income (RM)", fontsize=11)
    ax.set_ylabel("Gini Coefficient", fontsize=11)
    ax.set_title("Income vs Inequality at District Level (2022)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=7, ncol=3, loc="upper right")
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


# ─── Master runner ────────────────────────────────────────────────────────────

def run_all(arima_results: dict = None, clustering_results: dict = None,
            df_kmeans: pd.DataFrame = None, gini_df: pd.DataFrame = None,
            poverty_wide: pd.DataFrame = None, df_district: pd.DataFrame = None):

    print("Running evaluation...")

    # Load from disk if not provided
    if arima_results is None:
        with open(os.path.join(MODELS_DIR, "arima_results.json")) as f:
            arima_results = json.load(f)
    if clustering_results is None:
        with open(os.path.join(MODELS_DIR, "clustering_results.json")) as f:
            clustering_results = json.load(f)
    if df_kmeans is None:
        df_kmeans = pd.read_csv(os.path.join(PROCESSED_DIR, "districts_kmeans_clustered.csv"))
    if gini_df is None:
        gini_df = pd.read_csv(os.path.join(PROCESSED_DIR, "gini_state_clean.csv"))
    if poverty_wide is None:
        poverty_wide = pd.read_csv(os.path.join(PROCESSED_DIR, "poverty_district_wide.csv"))
    if df_district is None:
        df_district = pd.read_csv(os.path.join(PROCESSED_DIR, "hies_district_clean.csv"))

    # Time series
    ts_df = ts_metrics_table(arima_results)
    print(f"  TS metrics saved. Mean RMSE={ts_df['RMSE'].mean():.4f}")
    plot_ts_metrics_comparison(ts_df, save_path=os.path.join(FIGURES_DIR, "eval_ts_metrics.png"))
    plot_gini_trends_all_states(gini_df, save_path=os.path.join(FIGURES_DIR, "eval_gini_trends.png"))

    # Clustering
    cl_df = cluster_metrics_table(clustering_results)
    print(f"  Clustering metrics:\n{cl_df.to_string(index=False)}")
    plot_poverty_cluster_boxplot(df_kmeans, save_path=os.path.join(FIGURES_DIR, "eval_poverty_cluster.png"))
    plot_poverty_change_heatmap(poverty_wide, save_path=os.path.join(FIGURES_DIR, "eval_poverty_change.png"))
    plot_income_vs_gini_scatter(df_district, save_path=os.path.join(FIGURES_DIR, "eval_income_gini_scatter.png"))

    print("  Evaluation complete. Figures saved to outputs/figures/")
    return ts_df, cl_df


if __name__ == "__main__":
    run_all()
