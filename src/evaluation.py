"""
Evaluation module.

Produces summary metrics tables and multi-panel comparison figures
for both the time series (ARIMA) and clustering analyses.
Also generates fuel price vs CPI correlation and state CPI comparison charts.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "figures")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "models")


# ─── Time Series Evaluation ───────────────────────────────────────────────────

def ts_metrics_table(arima_result: dict) -> pd.DataFrame:
    m = arima_result["metrics"]
    order = arima_result["arima_order"]
    forecast_vals = arima_result["forecast"]["values"]
    baseline = arima_result.get("baseline", {}).get("metrics", {})
    rows = [{
        "Series": "Overall CPI Inflation (YoY)",
        "ARIMA Order": f"({order[0]},{order[1]},{order[2]})",
        "AIC": arima_result.get("aic", None),
        "BIC": arima_result.get("bic", None),
        "MAE": m["MAE"],
        "RMSE": m["RMSE"],
        "sMAPE (%)": m.get("sMAPE"),
        "MASE": m.get("MASE"),
        "Baseline RMSE (naive)": baseline.get("RMSE"),
        "Stationary (train)": arima_result["stationarity"]["is_stationary"],
        "Forecast End (avg %)": round(np.mean(forecast_vals[-6:]), 2),
    }]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(MODELS_DIR, "ts_metrics_summary.csv"), index=False)
    return df


def plot_fuel_cpi_correlation(fuel_corr: dict, save_path: str = None):
    """
    Dual-panel: fuel price vs CPI scatter + bar chart of correlations.
    """
    merged = pd.DataFrame(fuel_corr["merged_data"])
    merged["date"] = pd.to_datetime(merged["date"])

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Fuel Price vs CPI Inflation Correlation", fontsize=13, fontweight="bold")

    # Scatter: avg_fuel vs inflation_yoy
    ax = axes[0]
    ax.scatter(merged["avg_fuel"], merged["inflation_yoy"],
               alpha=0.55, s=35, color="steelblue", edgecolors="white", linewidths=0.3)
    slope, intercept, r, p, _ = stats.linregress(merged["avg_fuel"], merged["inflation_yoy"])
    x_line = np.linspace(merged["avg_fuel"].min(), merged["avg_fuel"].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, "r--", linewidth=1.5,
            label=f"OLS  r={r:.3f}  p={p:.3f}")
    ax.set_xlabel("Average Fuel Price (RM/litre)", fontsize=11)
    ax.set_ylabel("Overall CPI Inflation YoY (%)", fontsize=11)
    ax.set_title("Fuel Price vs Inflation (contemporaneous)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.25)

    # Bar: contemporaneous and lag-1 correlations per fuel type
    ax2 = axes[1]
    corr_data = fuel_corr["correlations"]
    fuel_types = list(corr_data.keys())
    contemp = [corr_data[f]["contemporaneous"] for f in fuel_types]
    lag1 = [corr_data[f]["lag1"] for f in fuel_types]
    x = np.arange(len(fuel_types))
    w = 0.35
    ax2.bar(x - w / 2, contemp, w, label="Contemporaneous", color="steelblue")
    ax2.bar(x + w / 2, lag1, w, label="Lag-1 (fuel leads inflation)", color="coral")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f.upper() for f in fuel_types], rotation=20)
    ax2.set_ylabel("Pearson Correlation (r)")
    ax2.set_title("Correlation by Fuel Type")
    ax2.axhline(y=0, color="black", linewidth=0.8)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_state_cpi_comparison(cpi_state_df: pd.DataFrame, save_path: str = None):
    """
    Horizontal bar chart comparing each state's overall CPI growth rate
    from the earliest to latest available month.
    """
    overall = cpi_state_df[cpi_state_df["division"] == "overall"].copy()

    def growth(grp):
        grp = grp.sort_values("date")
        if len(grp) < 2:
            return np.nan
        return (grp["index"].iloc[-1] - grp["index"].iloc[0]) / grp["index"].iloc[0] * 100

    growth_df = overall.groupby("state").apply(growth).reset_index()
    growth_df.columns = ["state", "cpi_growth_pct"]
    growth_df = growth_df.sort_values("cpi_growth_pct", ascending=True).dropna()

    fig, ax = plt.subplots(figsize=(9, 7))
    colors = ["#2166ac" if v < growth_df["cpi_growth_pct"].median() else "#d73027"
              for v in growth_df["cpi_growth_pct"]]
    ax.barh(growth_df["state"], growth_df["cpi_growth_pct"], color=colors)
    ax.axvline(x=growth_df["cpi_growth_pct"].median(), color="black", linestyle="--",
               linewidth=1, label=f"Median={growth_df['cpi_growth_pct'].median():.1f}%")
    ax.set_xlabel("CPI Growth Rate (%)", fontsize=11)
    ax.set_title("Overall CPI Growth by State (2010 → Latest)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_division_inflation_heatmap(cpi_inflation_df: pd.DataFrame, save_path: str = None):
    """
    Heatmap: rows = divisions, columns = years, values = mean annual yoy inflation.
    Excludes 'overall' to focus on component breakdown.
    """
    df = cpi_inflation_df[cpi_inflation_df["division"] != "overall"].dropna(subset=["inflation_yoy"])
    df = df[df["year"] >= 2010].copy()

    pivot = df.pivot_table(index="division_label", columns="year",
                           values="inflation_yoy", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(16, 7))
    sns.heatmap(pivot, cmap="RdYlGn_r", center=0, annot=True, fmt=".1f",
                linewidths=0.4, ax=ax, cbar_kws={"label": "Mean YoY Inflation (%)"})
    ax.set_title("CPI Division Inflation Heatmap (Annual Mean YoY %)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("")
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


def plot_income_vs_cpi_scatter(state_features_df: pd.DataFrame, save_path: str = None):
    """Scatter of state income vs CPI growth, coloured by cluster label."""
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = sorted(state_features_df["cluster_label"].unique())
    palette = sns.color_palette("tab10", len(labels))
    color_map = dict(zip(labels, palette))

    for label in labels:
        grp = state_features_df[state_features_df["cluster_label"] == label]
        ax.scatter(grp["income_mean_latest"], grp["cpi_growth_rate"],
                   label=label, color=color_map[label], s=90,
                   alpha=0.8, edgecolors="white", linewidths=0.4)
        for _, row in grp.iterrows():
            ax.annotate(row["state"], (row["income_mean_latest"], row["cpi_growth_rate"]),
                        fontsize=7, ha="left", va="bottom",
                        xytext=(4, 3), textcoords="offset points")

    ax.set_xlabel("Latest Mean Household Income (RM)", fontsize=11)
    ax.set_ylabel("CPI Growth Rate (%)", fontsize=11)
    ax.set_title("State Income vs CPI Growth (coloured by cluster)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


# ─── Master runner ────────────────────────────────────────────────────────────

def run_all(arima_results: dict = None, clustering_results: dict = None,
            df_kmeans: pd.DataFrame = None, cpi_state_df: pd.DataFrame = None,
            cpi_inflation_df: pd.DataFrame = None, state_features_df: pd.DataFrame = None):

    print("Running evaluation...")

    if arima_results is None:
        with open(os.path.join(MODELS_DIR, "arima_results.json")) as f:
            arima_results = json.load(f)
    if clustering_results is None:
        with open(os.path.join(MODELS_DIR, "clustering_results.json")) as f:
            clustering_results = json.load(f)
    if df_kmeans is None:
        df_kmeans = pd.read_csv(os.path.join(PROCESSED_DIR, "states_kmeans_clustered.csv"))
    if cpi_state_df is None:
        cpi_state_df = pd.read_csv(os.path.join(PROCESSED_DIR, "cpi_state_clean.csv"),
                                   parse_dates=["date"])
    if cpi_inflation_df is None:
        cpi_inflation_df = pd.read_csv(os.path.join(PROCESSED_DIR, "cpi_inflation_clean.csv"),
                                       parse_dates=["date"])
    if state_features_df is None:
        sf = pd.read_csv(os.path.join(PROCESSED_DIR, "state_features.csv"))
        state_features_df = sf.merge(df_kmeans[["state", "cluster_label"]], on="state", how="left")

    # Time series metrics
    ts_df = ts_metrics_table(arima_results)
    print(f"  TS metrics saved — RMSE={ts_df['RMSE'].iloc[0]} MASE={ts_df['MASE'].iloc[0]}")

    # Fuel correlation plot (if available)
    fuel_corr_path = os.path.join(MODELS_DIR, "fuel_correlation.json")
    if os.path.exists(fuel_corr_path):
        with open(fuel_corr_path) as f:
            fuel_corr = json.load(f)
        plot_fuel_cpi_correlation(
            fuel_corr,
            save_path=os.path.join(FIGURES_DIR, "eval_fuel_cpi_correlation.png"),
        )

    # State CPI comparison
    plot_state_cpi_comparison(
        cpi_state_df,
        save_path=os.path.join(FIGURES_DIR, "eval_state_cpi_comparison.png"),
    )

    # Division inflation heatmap
    plot_division_inflation_heatmap(
        cpi_inflation_df,
        save_path=os.path.join(FIGURES_DIR, "eval_division_heatmap.png"),
    )

    # Clustering metrics
    cl_df = cluster_metrics_table(clustering_results)
    print(f"  Clustering metrics:\n{cl_df.to_string(index=False)}")

    # Income vs CPI scatter (with cluster colour)
    if "cluster_label" in state_features_df.columns:
        plot_income_vs_cpi_scatter(
            state_features_df,
            save_path=os.path.join(FIGURES_DIR, "eval_income_vs_cpi.png"),
        )

    print("  Evaluation complete. Figures saved to outputs/figures/")
    return ts_df, cl_df


if __name__ == "__main__":
    run_all()
