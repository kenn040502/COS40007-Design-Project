"""
Master pipeline runner for Theme 3: Smart Government.
Runs: preprocessing -> time series -> clustering -> evaluation
Then launches the Flask dashboard (unless --no-dashboard is passed).

Datasets used:
  cpi_2d_inflation.csv  - Monthly national CPI inflation by division
  cpi_2d_state.csv      - Monthly CPI index by state and division
  fuelprice.csv         - Weekly retail fuel prices
  hh_income_state.csv   - Survey-based household income by state
"""

import sys
import os

# Always run from the project root, regardless of where Python was invoked from
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Point matplotlib at the pre-built font cache committed with the repo.
# This avoids the 2-3 minute "building font cache" step on cold Render starts.
os.environ.setdefault(
    "MPLCONFIGDIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "mpl_cache"),
)

from src.preprocessing import run_all as preprocess
from src.time_series import run_all as run_ts
from src.clustering import run_all as run_clustering
from src.evaluation import run_all as run_evaluation


def main():
    root = os.path.dirname(__file__)
    os.makedirs(os.path.join(root, "outputs", "figures"), exist_ok=True)
    os.makedirs(os.path.join(root, "outputs", "models"), exist_ok=True)
    os.makedirs(os.path.join(root, "data", "processed"), exist_ok=True)

    print("=" * 65)
    print("  THEME 3: SMART GOVERNMENT — MALAYSIAN COST OF LIVING AI")
    print("=" * 65)

    print("\n[1/4] Preprocessing...")
    cpi_inflation, cpi_state, fuelprice, income_state, overall_inflation, state_features = preprocess()

    print("\n[2/4] Time Series Forecasting (ARIMA — National CPI Inflation)...")
    arima_results = run_ts(overall_inflation, fuelprice)

    print("\n[3/4] Clustering (K-Means + Hierarchical — Malaysian States)...")
    cluster_results = run_clustering(state_features)

    print("\n[4/4] Evaluation & Visualisation...")
    run_evaluation(
        arima_results=arima_results,
        clustering_results=cluster_results,
        df_kmeans=cluster_results["df_kmeans"],
        cpi_state_df=cpi_state,
        cpi_inflation_df=cpi_inflation,
        state_features_df=cluster_results["df_kmeans"],
    )

    figures_dir = os.path.join(root, "outputs", "figures")
    print("\n" + "=" * 65)
    print("  Pipeline complete!")
    print(f"  Figures : outputs/figures/  ({len(os.listdir(figures_dir))} files)")
    print(f"  Models  : outputs/models/")
    print(f"  Data    : data/processed/")
    print("=" * 65)

    if "--no-dashboard" in sys.argv:
        return

    print("\nStarting Streamlit dashboard at http://localhost:8501 ...")
    print("Press Ctrl+C to stop.\n")
    import subprocess
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(root, "app", "streamlit_app.py"),
        "--server.port=8501",
        "--server.headless=true",
    ])


if __name__ == "__main__":
    main()
