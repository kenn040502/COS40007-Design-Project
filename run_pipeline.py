"""
Master pipeline runner for Theme 3: Smart Government.
Runs: preprocessing -> time series -> clustering -> evaluation
Then launches the Flask dashboard.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.preprocessing import run_all as preprocess
from src.time_series import run_all as run_ts
from src.clustering import run_all as run_clustering
from src.evaluation import run_all as run_evaluation


def main():
    print("=" * 65)
    print("  THEME 3: SMART GOVERNMENT — SOCIOECONOMIC AI ANALYSER")
    print("=" * 65)

    print("\n[1/4] Preprocessing...")
    hies_district, hies_state, poverty_long, poverty_wide, gini_state, gini_annual = preprocess()

    print("\n[2/4] Time Series Forecasting (ARIMA)...")
    arima_results = run_ts(gini_annual)

    print("\n[3/4] Clustering (K-Means + Hierarchical)...")
    cluster_results = run_clustering(hies_district)

    print("\n[4/4] Evaluation & Visualisation...")
    run_evaluation(
        arima_results=arima_results,
        clustering_results=cluster_results,
        df_kmeans=cluster_results["df_kmeans"],
        gini_df=gini_state,
        poverty_wide=poverty_wide,
        df_district=hies_district,
    )

    print("\n" + "=" * 65)
    print("  Pipeline complete!")
    print(f"  Figures : outputs/figures/  ({len(os.listdir('outputs/figures'))} files)")
    print(f"  Models  : outputs/models/")
    print(f"  Data    : data/processed/")
    print("=" * 65)

    # Launch dashboard
    print("\nStarting web dashboard at http://localhost:5050 ...")
    print("Press Ctrl+C to stop.\n")
    from app.dashboard import app
    app.run(debug=False, port=5050)


if __name__ == "__main__":
    main()
