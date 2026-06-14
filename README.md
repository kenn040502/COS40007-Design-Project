# Malaysian Cost of Living AI — Smart Government

An end-to-end machine learning system that forecasts Malaysia's national CPI inflation, analyses the relationship between fuel prices and inflation, and clusters the 16 Malaysian states by economic indicators. Built for COS40007 Design Project (Theme 3: Smart Government).

---

## Overview

| Module | Technique | Output |
|---|---|---|
| Time Series Forecasting | ARIMA (BIC-selected) + SARIMAX | 24-month national CPI forecast |
| State Clustering | K-Means + Hierarchical (Ward) | State economic groupings |
| Fuel–Inflation Analysis | Correlation + exogenous ARIMA | Fuel price impact on CPI |
| Dashboard | Streamlit | Interactive 4-tab web app |

---

## Datasets

All data sourced from [OpenDOSM](https://open.dosm.gov.my/) — Malaysia's official open data portal.

| File | Description |
|---|---|
| `cpi_2d_inflation.csv` | Monthly national CPI inflation by division |
| `cpi_2d_state.csv` | Monthly CPI index by state and division |
| `fuelprice.csv` | Weekly retail prices for RON95, RON97, Diesel |
| `hh_income_state.csv` | Survey-based household income by state |

---

## Project Structure

```
COS40007-Design-Project/
├── src/
│   ├── preprocessing.py      # Data cleaning and feature engineering
│   ├── time_series.py        # ARIMA forecasting
│   ├── clustering.py         # K-Means + Hierarchical clustering
│   └── evaluation.py         # Metrics, correlation analysis, visualisations
├── app/
│   └── streamlit_app.py      # Interactive dashboard
├── data/
│   ├── raw/                  # Original CSVs from OpenDOSM
│   └── processed/            # Cleaned and merged datasets
├── outputs/
│   ├── figures/              # Charts and plots (PNG)
│   └── models/               # Saved model results (JSON, PKL, CSV)
├── run_pipeline.py           # Master pipeline runner
├── requirements.txt
└── README.md
```

---

## Setup

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
```

---

## Running

### Full pipeline + dashboard

```bash
python run_pipeline.py
```

Runs preprocessing → forecasting → clustering → evaluation, then launches the Streamlit dashboard at `http://localhost:8501`.

### Pipeline only (no dashboard)

```bash
python run_pipeline.py --no-dashboard
```

### Dashboard only (pre-built outputs required)

```bash
streamlit run app/streamlit_app.py
```

### Convenience scripts

```bash
# Windows
run.bat

# macOS / Linux
bash run.sh
```

---

## Pipeline Steps

1. **Preprocessing** — cleans raw CSVs, handles missing values, aligns monthly/weekly frequencies, engineers state-level features
2. **Time Series Forecasting** — selects ARIMA order via BIC, fits on national CPI, evaluates on last 24 months, forecasts 24 months ahead; also fits SARIMAX with fuel price as exogenous input
3. **Clustering** — standardises 5 state features, runs K-Means (elbow + silhouette for k selection) and Agglomerative (Ward linkage), reduces to 2D via PCA for visualisation
4. **Evaluation** — computes MAE, RMSE for forecasting; Silhouette, Davies-Bouldin, Calinski-Harabasz for clustering; generates all figures

---

## Clustering Features

| Feature | Description |
|---|---|
| `mean_cpi_index` | Average CPI level across full period |
| `cpi_growth_rate` | % CPI growth from earliest to latest month |
| `cpi_volatility` | Std dev of monthly CPI (price stability proxy) |
| `income_mean_latest` | Most recent mean household income |
| `income_median_latest` | Most recent median household income |

---

## Dashboard Tabs

- **Overview** — project summary and dataset snapshot
- **Time Series Forecast** — ARIMA forecast with confidence intervals, forecast table
- **State Clustering** — PCA scatter plots, cluster profiles, dendrogram
- **Fuel Analysis** — fuel–CPI correlation heatmap, SARIMAX vs baseline comparison

---

## Outputs

After running the pipeline:

| Path | Contents |
|---|---|
| `outputs/figures/` | 10 PNG charts (forecast, clusters, correlation, etc.) |
| `outputs/models/arima_results.json` | ARIMA order, metrics, forecast values |
| `outputs/models/clustering_results.json` | Cluster assignments and metrics |
| `outputs/models/ts_metrics_summary.csv` | MAE / RMSE per model |
| `outputs/models/cluster_metrics_summary.csv` | Silhouette / DB / CH per method |
| `data/processed/` | Cleaned CSVs ready for dashboard |
