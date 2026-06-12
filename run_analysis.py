"""
Headless analysis runner: runs the full pipeline (preprocessing -> time series
-> clustering -> evaluation) WITHOUT launching the Flask dashboard.
Used for batch/automated regeneration of all outputs.
Run the interactive dashboard separately with `python run_pipeline.py` or
`python app/dashboard.py`.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.preprocessing import run_all as preprocess
from src.time_series import run_all as run_ts
from src.clustering import run_all as run_clustering
from src.evaluation import run_all as run_evaluation


def main():
    print("=" * 65)
    print("  THEME 3: SMART GOVERNMENT — ANALYSIS PIPELINE (headless)")
    print("=" * 65)

    print("\n[1/4] Preprocessing...")
    hies_district, hies_state, poverty_long, poverty_wide, gini_state, gini_annual = preprocess()

    print("\n[2/4] Time Series Forecasting (ARIMA)...")
    arima_results = run_ts(gini_annual)

    print("\n[3/4] Clustering (K-Means + Hierarchical)...")
    cluster_results = run_clustering(hies_district)

    print("\n[4/4] Evaluation & Visualisation...")
    ts_df, cl_df = run_evaluation(
        arima_results=arima_results,
        clustering_results=cluster_results,
        df_kmeans=cluster_results["df_kmeans"],
        gini_df=gini_state,
        poverty_wide=poverty_wide,
        df_district=hies_district,
    )

    print("\n" + "=" * 65)
    print("  Pipeline complete!")
    figs = len(os.listdir(os.path.join(os.path.dirname(__file__), "outputs", "figures")))
    print(f"  Figures : outputs/figures/  ({figs} files)")
    print(f"  TS mean RMSE  = {ts_df['RMSE'].mean():.4f}")
    print(f"  TS mean MAPE  = {ts_df['MAPE (%)'].mean():.2f}%")
    print(f"  Clustering best k = {cluster_results['best_k']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
