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
    cpi_inflation, cpi_state, fuelprice, income_state, overall_inflation, state_features = preprocess()

    print("\n[2/4] Time Series Forecasting (ARIMA)...")
    arima_results = run_ts(overall_inflation, fuelprice)

    print("\n[3/4] Clustering (K-Means + Hierarchical)...")
    cluster_results = run_clustering(state_features)

    print("\n[4/4] Evaluation & Visualisation...")
    ts_df, cl_df = run_evaluation(
        arima_results=arima_results,
        clustering_results=cluster_results,
        df_kmeans=cluster_results["df_kmeans"],
        cpi_state_df=cpi_state,
        cpi_inflation_df=cpi_inflation,
        state_features_df=state_features,
    )

    print("\n" + "=" * 65)
    print("  Pipeline complete!")
    figs = len(os.listdir(os.path.join(os.path.dirname(__file__), "outputs", "figures")))
    print(f"  Figures : outputs/figures/  ({figs} files)")
    print(f"  TS RMSE   = {ts_df['RMSE'].iloc[0]:.4f}")
    print(f"  TS MAPE   = {ts_df['MAPE (%)'].iloc[0]:.2f}%")
    print(f"  Clustering best k = {cluster_results['best_k']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
