# COS40007 Design Project — Theme 3: Smart Government

## Project Overview

**Subject:** COS40007 Design Project 2026  
**Theme:** Theme 3 — Smart Government  
**AI Areas:** Machine Learning, Predictive Analytics, Time Series Forecasting, Clustering  
**Topic:** Analyzing Malaysian Public Sector Data Using Time Series and Clustering Techniques  
**Data Source:** OpenDOSM Data Catalogue (CC BY 4.0), Department of Statistics Malaysia (DOSM)

The system answers four key questions defined in `KEY_QUESTIONS.md`:
1. Which OpenDOSM datasets were selected and what are their key features?
2. What time series / clustering methods were applied and why?
3. What patterns, trends, or groupings were discovered?
4. What are the policy implications?

---

## Repository Structure

```
COS40007-Design-Project/
├── run_pipeline.py              # Master runner: preprocess → TS → clustering → eval → dashboard
├── requirements.txt
├── KEY_QUESTIONS.md             # Answers to assignment brief questions
├── SKILL.md                     # Codebase assistant skill definition (explore/review/debug/test/simplify)
│
├── data/
│   ├── download_datasets.py     # Downloads 4 raw CSVs from DOSM storage URLs
│   ├── raw/                     # Source CSVs (git-ignored if large; re-download with download_datasets.py)
│   │   ├── hies_district.csv
│   │   ├── hies_state.csv
│   │   ├── hh_poverty_district.csv
│   │   └── hh_inequality_state.csv
│   └── processed/               # Cleaned/transformed CSVs written by preprocessing.py
│
├── src/
│   ├── preprocessing.py         # Stage 1: load, clean, engineer features, interpolate Gini series
│   ├── time_series.py           # Stage 2: ARIMA(2,1,2) per state, train/test split, 2023–2030 forecast
│   ├── clustering.py            # Stage 3: K-Means + Agglomerative (Ward), PCA, elbow/silhouette/DB
│   └── evaluation.py            # Stage 4: metrics tables, multi-panel comparison figures
│
├── app/
│   ├── dashboard.py             # Flask app — 4-tab dashboard (Overview / TS / Clustering / Poverty)
│   └── templates/index.html
│
└── outputs/
    ├── figures/                 # All PNG plots (static files served by Flask)
    └── models/                  # arima_results.json, clustering_results.json, *_metrics_summary.csv
```

---

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Download raw data (first-time setup)
python data/download_datasets.py

# Run full pipeline and launch dashboard at http://localhost:5050
python run_pipeline.py

# Run individual stages (can be run standalone)
python src/preprocessing.py
python src/time_series.py
python src/clustering.py
python src/evaluation.py

# Launch dashboard only (requires pipeline to have been run first)
python app/dashboard.py
```

---

## Pipeline Stages

### Stage 1 — Preprocessing (`src/preprocessing.py`)
- Loads 4 raw CSVs, parses dates, coerces numeric types, drops NaN rows.
- Engineers `savings_rate` and `income_expenditure_ratio` on the HIES district frame.
- Pivots poverty data into wide format (2019 vs 2022 columns + change columns).
- Interpolates irregular Gini survey years (1974–2022) to a uniform annual series using linear interpolation — this is required for ARIMA.
- Outputs 6 DataFrames and writes 6 processed CSVs to `data/processed/`.

### Stage 2 — Time Series (`src/time_series.py`)
- Model: `ARIMA(2, 1, 2)` from `statsmodels`.
- Per-state loop: ADF stationarity test → train/test split (last 5 obs held out) → fit on train → evaluate on test (MAE, RMSE, MAPE) → refit on full series → forecast 2023–2030.
- Saves per-state PNG plots and a summary bar chart to `outputs/figures/`.
- Saves all results to `outputs/models/arima_results.json`.

### Stage 3 — Clustering (`src/clustering.py`)
- Feature matrix: `income_mean`, `income_median`, `expenditure_mean`, `gini`, `poverty` (5 features, 160 districts).
- All features standardised with `StandardScaler` before fitting.
- Optimal k selection: Elbow (WCSS inertia), Silhouette score, and Davies-Bouldin index over k=2–10; best k selected by highest silhouette. Current result: **k=2**.
- Algorithms: `KMeans(n_clusters=k, random_state=42)` and `AgglomerativeClustering(linkage="ward")`.
- PCA (2 components) for scatter plot visualisation.
- Clusters assigned semantic labels by ordering on mean income (ascending).
- Saves clustered CSVs, PCA plots, profile heatmap, and dendrogram to outputs.

### Stage 4 — Evaluation (`src/evaluation.py`)
- Compiles ARIMA metrics across all 16 states into a CSV table.
- Plots 3-panel ARIMA error comparison (MAE/RMSE/MAPE per state).
- Plots historical Gini trends (1974–2022) for all states.
- Cluster metrics table (Silhouette, Davies-Bouldin, Calinski-Harabasz for both methods).
- Box plots of poverty and income by cluster, poverty change heatmap (2019→2022), income vs Gini scatter.

### Dashboard (`app/dashboard.py`)
- Flask server on port 5050.
- Serves static PNG figures from `outputs/figures/` via `/figure/<filename>`.
- JSON API endpoints for dynamic content:
  - `GET /api/overview` — state-level HIES summary
  - `GET /api/ts/states` — list of states with successful ARIMA fits
  - `GET /api/ts/forecast?state=<name>` — per-state forecast data
  - `GET /api/ts/metrics` — ARIMA metrics table
  - `GET /api/cluster/districts[?state=<name>]` — K-Means clustered districts
  - `GET /api/cluster/metrics` — cluster evaluation scores
  - `GET /api/poverty/districts[?state=<name>]` — poverty change by district
  - `GET /api/poverty/states` — state list

---

## Data Sources & Key Facts

| Dataset | File | Coverage | Rows | Primary use |
|---------|------|----------|------|-------------|
| HIES by District | `hies_district.csv` | 160 districts, 2022 | 160 | Clustering |
| HIES by State | `hies_state.csv` | 16 states, 2022 | 16 | Overview |
| Poverty by District | `hh_poverty_district.csv` | 160 districts, 2019–2022 | ~318 | Poverty analysis |
| Gini by State | `hh_inequality_state.csv` | 16 states, 1974–2022 | 273 | Time series |

All datasets are licensed **CC BY 4.0** — cite DOSM in any report.

**Important constraint:** Dataset selection and scope changes must be approved by **Dr Joel** before finalising.

---

## Key Results (Current Run)

- **Clustering:** k=2 — 75.6% of districts (121/160) are Low Income/High Poverty (mean RM 5,018, 14.82% poverty); 24.4% (39) are Mid-Low Income (mean RM 8,938, 3.68% poverty). Silhouette = 0.4213.
- **Time Series:** Mean RMSE = 0.0144, Mean MAPE ≈ 3.6% across 16 states. National Gini fell from 0.498 (1974) to 0.359 (2022); most states forecast to continue declining by 2030. Kelantan alone shows a slightly rising forecast.
- **Poverty change:** Sarawak rural districts dominate both the largest increases and decreases (2019→2022), indicating commodity-cycle volatility.

---

## How to Work on This Project with Claude

This project has a SKILL.md file defining five focused modes for code assistance. Use them as follows:

| Task | Mode to invoke |
|------|----------------|
| Understanding what a module does | `explore` |
| Checking a change for correctness or risks | `code-review` |
| Debugging a pipeline error or bad forecast | `debugger` |
| Deciding what tests to write | `test-engineer` |
| Cleaning up or refactoring a module | `code-simplifier` |

### Preferred approach for common tasks

**Adding a new model (e.g., SARIMA, Prophet):**
1. Add a new function to `src/time_series.py` following the `fit_arima` / `run_forecast_all_states` pattern.
2. Save results to `outputs/models/` as JSON.
3. Add a plot function following the `plot_forecast` pattern.
4. Expose results via a new `/api/ts/<endpoint>` in `app/dashboard.py`.

**Adding a new clustering algorithm:**
1. Add a `fit_<algo>` function to `src/clustering.py`.
2. Reuse `pca_transform`, `assign_semantic_labels`, and `plot_clusters_pca`.
3. Add its scores to the `result` dict returned by `run_all`.

**Adding a new dataset:**
1. Add download entry to `data/download_datasets.py`.
2. Add a `load_<dataset>` function to `src/preprocessing.py`.
3. Return the new DataFrame from `preprocessing.run_all()` and thread it into `run_pipeline.py`.

**Modifying ARIMA order:**
- Change `ARIMA_ORDER = (p, d, q)` at the top of `src/time_series.py`.
- Re-run `python src/time_series.py` to regenerate results.

### Style rules
- No comments unless the WHY is non-obvious.
- No docstrings beyond a single short line.
- Each `src/*.py` module is independently runnable (`if __name__ == "__main__": run_all()`).
- All plots use `matplotlib.use("Agg")` — never call `plt.show()` in pipeline code.
- All output paths are built with `os.path.join` from module-level `*_DIR` constants.

### Testing
There is no formal test suite. To verify a stage works:
```bash
python src/preprocessing.py   # check data/processed/ files are written
python src/time_series.py     # check outputs/models/arima_results.json
python src/clustering.py      # check outputs/models/clustering_results.json
python src/evaluation.py      # check outputs/figures/ PNGs
```

---

## Assignment Context

- **Unit:** COS40007 Design Project 2026, Swinburne University of Technology
- **Theme:** 3 — Smart Government
- **Deliverables:** AI model pipeline + visualisations + comprehensive report
- **Key report sections:** Methodology, Results, Policy Implications
- **Approval required:** Dr Joel must approve dataset choices before finalising scope
- **Data licence:** CC BY 4.0 — must attribute DOSM in report
