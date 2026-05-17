# COS40007 Design Project — Theme 3: Smart Government

Analyzing Malaysian Public Sector Data Using Time Series and Clustering Techniques.

**Data:** OpenDOSM / Department of Statistics Malaysia (DOSM) — CC BY 4.0  
**Methods:** ARIMA(2,1,2) time series forecasting · K-Means + Hierarchical clustering  
**Dashboard:** Interactive Flask web app with Plotly charts

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download raw datasets

```bash
python data/download_datasets.py
```

Downloads 4 CSV files from DOSM into `data/raw/`:

| File | Description |
|------|-------------|
| `hies_district.csv` | Household income/expenditure/poverty by district (2022) |
| `hies_state.csv` | Household income/expenditure/poverty by state (1970–2022) |
| `hh_poverty_district.csv` | Absolute & relative poverty by district (2019–2022) |
| `hh_inequality_state.csv` | Gini coefficient by state (1974–2022) |

### 3. Run the full pipeline and launch dashboard

```bash
python run_pipeline.py
```

Opens the dashboard at **http://localhost:5050**

---

## Running stages individually

```bash
python src/preprocessing.py   # clean data → data/processed/
python src/time_series.py     # ARIMA forecasts → outputs/models/ + outputs/figures/
python src/clustering.py      # K-Means + Hierarchical → outputs/models/ + outputs/figures/
python src/evaluation.py      # summary metrics + figures
python app/dashboard.py       # dashboard only (pipeline must have been run first)
```

---

## Project Structure

```
├── run_pipeline.py          # Master runner (pipeline + dashboard)
├── requirements.txt
│
├── data/
│   ├── download_datasets.py # Download raw CSVs from DOSM
│   ├── raw/                 # Source CSVs (download with script above)
│   └── processed/           # Cleaned/transformed CSVs (generated)
│
├── src/
│   ├── preprocessing.py     # Load, clean, feature engineering, Gini interpolation
│   ├── time_series.py       # ARIMA(2,1,2) per state, train/test eval, 2023–2030 forecast
│   ├── clustering.py        # K-Means + Ward hierarchical, PCA, elbow/silhouette/DB
│   └── evaluation.py        # Metrics tables and comparison figures
│
├── app/
│   ├── dashboard.py         # Flask app — 4 tabs, JSON API, Plotly charts
│   └── templates/index.html
│
└── outputs/
    ├── figures/             # PNG plots (served by dashboard)
    └── models/              # arima_results.json, clustering_results.json, metric CSVs
```

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| **Overview** | State-level income/poverty bar chart, Gini trend lines |
| **Time Series Forecast** | Per-state ARIMA forecast (interactive state selector), metrics table |
| **District Clustering** | K-Means PCA scatter, cluster profiles, dendrogram, metrics table |
| **Poverty Analysis** | 2019 vs 2022 poverty scatter, district-level data table |

---

## Key Results

- **75.6%** of Malaysian districts (121/160) are low-income/high-poverty (mean RM 5,018, poverty 14.82%)
- National Gini fell from **0.498** (1974) to **0.359** (2022); forecast continues declining for most states by 2030
- **Kelantan** is the only state with a rising Gini forecast (0.385 → 0.391 by 2030)
- ARIMA mean RMSE = **0.0144**, mean MAPE ≈ **3.6%** across 16 states

---

## Data Licence

All datasets are from the [OpenDOSM Data Catalogue](https://open.dosm.gov.my) and licensed under  
**Creative Commons Attribution 4.0 International (CC BY 4.0)** — cite DOSM in any report.
