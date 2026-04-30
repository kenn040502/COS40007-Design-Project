# Theme 3: Smart Government — Key Questions & Answers

**COS40007 Design Project 2026**
**Topic:** Analyzing Malaysian Public Sector Data Using Time Series and Clustering Techniques
**Data Source:** OpenDOSM / Department of Statistics Malaysia (DOSM)

---

## Question 1: Which datasets from OpenDOSM were selected, and what are their key features?

### Datasets Selected

Four datasets were sourced from the OpenDOSM Data Catalogue (CC BY 4.0):

| Dataset | Source URL | Coverage | Rows |
|---------|-----------|----------|------|
| HIES by District | `open.dosm.gov.my/data-catalogue/hies_district` | 160 districts, 2022 | 160 |
| HIES by State | `open.dosm.gov.my/data-catalogue/hies_state` | 16 states, 2022 | 16 |
| Poverty by District | `data.gov.my/data-catalogue/hh_poverty_district` | 160 districts, 2019–2022 | 318 |
| Gini Coefficient by State | `open.dosm.gov.my/data-catalogue/hh_inequality_state` | 16 states, 1974–2022 | 273 |

### Key Features

**HIES by District** — the primary clustering dataset — contains seven variables per district:
- `income_mean` and `income_median` (RM): Household gross monthly income
- `expenditure_mean` (RM): Household monthly expenditure
- `gini`: Gini coefficient measuring within-district income inequality (0–1 scale)
- `poverty`: Absolute poverty rate (% of households below the Poverty Line Income)

Two engineered features were added during preprocessing:
- `savings_rate = (income_mean - expenditure_mean) / income_mean × 100`
- `income_expenditure_ratio = income_mean / expenditure_mean`

**Gini Coefficient by State** — the primary time series dataset — contains:
- `state`: One of 16 states/Federal Territories
- `year`: Survey year (irregular intervals, 1974–2022)
- `gini`: State-level Gini coefficient

Because the HIES is not conducted annually, the Gini series contains gaps (e.g., 1974, 1976, 1979, 1984…). Linear interpolation was applied to produce a uniform annual series (698 data points across 16 states) required for ARIMA modelling.

**Why these datasets?**
The combination of district-level cross-sectional data (suitable for clustering) and a long-run state-level time series (suitable for forecasting) directly aligns with the project brief of deriving policy-relevant insights on poverty and inequality in Malaysia.

---

## Question 2: What time series or clustering methods were applied, and why were they chosen?

### Time Series: ARIMA(2,1,2)

**Method:** AutoRegressive Integrated Moving Average with order (p=2, d=1, q=2).

**Why ARIMA?**
- The Gini series exhibits a clear downward long-run trend (national average fell from 0.498 in 1974 to 0.359 in 2022), which suggests non-stationarity — addressed by the differencing term d=1.
- ARIMA is well-suited for moderately long, univariate time series with trend and without strong seasonality, which describes the Gini data.
- It produces interpretable forecasts with confidence intervals, which is important for policy communication.
- An Augmented Dickey-Fuller (ADF) stationarity test was run on each state's training series before fitting to confirm the need for differencing.

**Evaluation strategy:**
- The last 5 observations per state were withheld as a test set.
- Metrics: MAE, RMSE, MAPE.
- After evaluation, the model was refit on the full series to produce a forecast for 2023–2030.

**Forecast horizon:** 2023–2030 (8 years), giving policy-makers a near-term planning window.

---

### Clustering: K-Means + Agglomerative Hierarchical (Ward Linkage)

**Method 1 — K-Means:** Partition-based clustering minimising within-cluster sum of squares (WCSS).

**Method 2 — Agglomerative Hierarchical (Ward):** Builds a cluster hierarchy by merging the pair of clusters that minimises total within-cluster variance at each step.

**Why two methods?**
Running both algorithms on the same data provides a cross-validation of the cluster structure. If K-Means and hierarchical clustering produce similar groupings and scores, the discovered clusters are likely genuine patterns rather than artefacts of one algorithm.

**Feature set and preprocessing:**
All five HIES district features (`income_mean`, `income_median`, `expenditure_mean`, `gini`, `poverty`) were standardised using `StandardScaler` before clustering to prevent high-magnitude income variables from dominating distance calculations.

**Optimal k selection:**
Three independent criteria were computed for k = 2 to 10:
- **Elbow method** (WCSS inertia): identifies the "elbow" point of diminishing returns.
- **Silhouette score** (higher is better): measures how well-separated clusters are.
- **Davies-Bouldin index** (lower is better): measures average cluster compactness and separation.

All three criteria agreed on **k = 2** as the optimal number of clusters.

**Visualisation:** Principal Component Analysis (PCA) was applied to reduce the 5-dimensional feature space to 2 principal components for scatter plot visualisation. PC1 and PC2 together captured the majority of variance, confirming that two components were sufficient for a meaningful 2-D projection.

---

## Question 3: What patterns, trends, or groupings were discovered through the analysis?

### 3.1 Time Series: Gini Coefficient Trends (1974–2022) and Forecast (2023–2030)

**Long-run national improvement:**
Malaysia's average Gini coefficient fell from **0.498 in 1974** to **0.359 in 2022**, a reduction of approximately 0.14 points over 48 years. This reflects the impact of affirmative economic policies (NEP, NDP, NEM) and sustained GDP growth in reducing income inequality.

**State-level forecast results (2030):**

| State | Gini 2022 | Forecast 2030 | Trend | RMSE |
|-------|-----------|---------------|-------|------|
| W.P. Kuala Lumpur | 0.3796 | 0.3763 | Stable | 0.0196 |
| Selangor | 0.3790 | 0.3537 | Declining | 0.0168 |
| Kelantan | 0.3854 | 0.3906 | Rising slightly | 0.0039 |
| Sabah | 0.4003 | 0.3947 | Declining | 0.0019 |
| Pahang | 0.3260 | 0.3031 | Declining fast | 0.0216 |
| Terengganu | 0.3303 | 0.3257 | Declining | 0.0173 |
| W.P. Labuan | 0.3763 | 0.2818 | Declining fast | 0.0555 |

**Key findings:**
- **Sabah** is the only state with a Gini above 0.40 in 2022 (0.4003), indicating persistently high inequality. The model forecasts a modest decline to 0.3947 by 2030.
- **Kelantan** shows a slightly rising forecast (0.3854 → 0.3906), signalling that inequality may be worsening in one of Malaysia's poorest states — a policy concern.
- **W.P. Labuan** has the highest forecast RMSE (0.0555, MAPE 16.49%), indicating high volatility in its Gini series and reduced forecast reliability for this territory.
- The majority of states are forecast to maintain or moderately reduce inequality by 2030, consistent with the long-run trend.
- Overall model performance was strong: **mean RMSE = 0.0144**, **mean MAPE ≈ 3.6%** across 16 states.

---

### 3.2 Clustering: District Socioeconomic Groupings

**Two distinct clusters were identified across 160 Malaysian districts:**

| Cluster | Districts | Mean Income (RM) | Poverty Rate (%) | Gini |
|---------|-----------|-----------------|-----------------|------|
| Low Income, High Poverty | 121 (75.6%) | 5,018 | 14.82 | 0.34 |
| Mid-Low Income | 39 (24.4%) | 8,938 | 3.68 | 0.34 |

**K-Means evaluation scores:**
- Silhouette = **0.4213** (moderate-to-good separation)
- Davies-Bouldin = **0.9347** (good compactness)
- Calinski-Harabasz = **113.62**

Hierarchical clustering produced nearly identical scores (Silhouette = 0.4159), confirming cluster validity.

**Key findings:**
- **121 districts (75.6%)** fall into the low-income, high-poverty cluster. These are predominantly located in Sabah, Sarawak, Kelantan, Kedah, and rural Peninsular Malaysia.
- **39 districts (24.4%)** are in the mid-income cluster, concentrated in the Klang Valley (Selangor, W.P. Kuala Lumpur), Johor Bahru, Penang, and Melaka corridors.
- Both clusters have similar Gini coefficients (≈0.34), meaning inequality within districts is comparable regardless of income level. The primary differentiating factor between clusters is **absolute income level and poverty rate**, not within-district inequality.
- This finding suggests Malaysia's inequality problem is primarily **between-district** (geographic economic disparity) rather than within-district, pointing to the need for region-targeted redistribution policies rather than broad progressive taxation alone.

---

### 3.3 Poverty Analysis: Change 2019 to 2022

The COVID-19 pandemic (2020–2021) had an uneven impact on poverty across districts.

**Districts with the largest poverty increase (2019–2022):**

| District | State | 2019 (%) | 2022 (%) | Change |
|----------|-------|----------|----------|--------|
| Julau | Sarawak | 13.0 | 31.2 | +18.2 pp |
| Tanjung Manis | Sarawak | 3.4 | 20.7 | +17.3 pp |
| Kapit | Sarawak | 3.8 | 20.6 | +16.8 pp |
| Daro | Sarawak | 18.5 | 32.5 | +14.0 pp |
| Belaga | Sarawak | 6.9 | 19.5 | +12.6 pp |

**Districts with the largest poverty decrease (2019–2022):**

| District | State | 2019 (%) | 2022 (%) | Change |
|----------|-------|----------|----------|--------|
| Bukit Mabong | Sarawak | 28.7 | 8.2 | -20.5 pp |
| Telupid | Sabah | 40.7 | 20.8 | -19.9 pp |
| Betong | Sarawak | 22.4 | 9.8 | -12.6 pp |
| Kuala Penyu | Sabah | 29.7 | 17.6 | -12.1 pp |
| Tebedu | Sarawak | 38.6 | 26.9 | -11.7 pp |

**Key findings:**
- Sarawak rural districts dominate both the largest poverty increases and decreases, reflecting high volatility in interior Borneo communities that are heavily dependent on commodity prices and agricultural income.
- Sabah's Telupid recorded a dramatic improvement (-19.9 pp), possibly linked to targeted rural development programs.
- The highest-income states (W.P. Kuala Lumpur, Selangor) showed minimal poverty change, confirming that urban economic resilience buffered the pandemic shock.

---

## Question 4: What are the policy implications of the findings?

### 4.1 Geographic Concentration of Poverty

The clustering results show that **75.6% of Malaysian districts are classified as low-income, high-poverty** with a mean poverty rate of 14.82%, compared to only 3.68% in the mid-income cluster. This strong geographic concentration — predominantly in Sabah, Sarawak, Kelantan, and Kedah — suggests that:

- **National average statistics mask severe regional inequality.** Policy instruments should be geographically targeted rather than uniform.
- The **District Development Index** or similar scoring frameworks used by the EPU (Economic Planning Unit) should incorporate the five clustering features (income, expenditure, Gini, poverty) to stratify districts and allocate development funds accordingly.

### 4.2 Kelantan's Rising Inequality Forecast

The ARIMA model forecasts Kelantan's Gini to increase slightly from 0.385 to 0.391 by 2030. Kelantan already has the **lowest mean income (RM 4,885)** and **highest poverty rate (13.2%)** among all states. A rising Gini in this context indicates that even within Kelantan, income is becoming more concentrated at the top — a compounding disadvantage. Policy interventions such as targeted cash transfer expansions (e.g., STR/Sumbangan Tunai Rahmah), skills training, and SME support in Kelantan should be prioritised.

### 4.3 Sabah — High Inequality Despite Improvement

Sabah remains the only state with a Gini above 0.40 (2022: 0.4003). Although the forecast shows a gradual decline to 0.3947 by 2030, this improvement is slow. Given Sabah also contains highly volatile poverty districts (e.g., Telupid with a 40.7% poverty rate in 2019), coordinated state and federal interventions are needed.

### 4.4 Sarawak's Poverty Volatility

Sarawak's rural interior districts exhibit the highest poverty volatility: the same state produced both the top 5 poverty increases and included several top decreases. This suggests structural dependence on commodity cycles (timber, palm oil, pepper). Diversification of rural livelihoods and strengthening social safety nets in Sarawak interior districts would reduce this vulnerability.

### 4.5 Positive National Trend

The 48-year national Gini trend (0.498 to 0.359) demonstrates that Malaysia's long-run development model has been effective in reducing income inequality at the aggregate level. The ARIMA forecasts for most states continue this downward trajectory through 2030, suggesting that existing policies are having the desired effect — but the pace of improvement in lagging states (Kelantan, Sabah) warrants accelerated action.

---

## Summary Table

| Analysis | Method | Key Finding |
|----------|--------|-------------|
| Time Series | ARIMA(2,1,2), 16 states | National Gini fell from 0.498 (1974) to 0.359 (2022); forecast continues declining to ~0.35 by 2030 for most states |
| Time Series | ARIMA evaluation | Mean RMSE = 0.0144, Mean MAPE = 3.6%; Kelantan alone shows rising forecast |
| Clustering | K-Means, k=2 | 75.6% of districts are low-income/high-poverty (mean RM 5,018, 14.82% poverty) vs 24.4% mid-income (mean RM 8,938, 3.68% poverty) |
| Clustering | Silhouette = 0.421 | Moderate-to-good cluster separation; results validated by hierarchical clustering |
| Poverty Analysis | Descriptive, 2019–2022 | Sarawak rural districts show highest poverty volatility; Sabah Telupid improved most (-19.9 pp) |

---

*Datasets licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). Department of Statistics Malaysia (DOSM).*
