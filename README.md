# AI-Based Malaysian Cost of Living Forecasting and State Clustering System

## Project Overview

This project focuses on analyzing Malaysian economic and household cost-of-living trends using machine learning, time series forecasting, and clustering techniques.

The project uses datasets from Malaysia's OpenDOSM open data portal to forecast inflation trends, analyze fuel price influence, and identify state-level economic patterns.

The final system should:
- Forecast future CPI inflation trends
- Analyze relationship between fuel prices and inflation
- Cluster Malaysian states based on economic indicators
- Provide interactive visualizations and dashboard outputs
- Support policy and socio-economic interpretation

---

# Selected Datasets

## 1. Monthly CPI Inflation by Division
Purpose:
- Main target variable for inflation forecasting
- Analyze inflation trends across categories

Possible Features:
- Date
- Division
- Inflation rate

---

## 2. Monthly CPI by State & Division
Purpose:
- Compare inflation across Malaysian states
- State-level clustering and trend analysis

Possible Features:
- State
- Division
- CPI index
- Date

---

## 3. Price of Petroleum & Diesel
Purpose:
- Analyze relationship between fuel prices and inflation
- External feature for multivariate forecasting

Possible Features:
- Weekly fuel price
- RON95
- RON97
- Diesel
- Date

---

## 4. Household Income by State
Purpose:
- Compare income levels against inflation pressure
- Additional clustering feature

Possible Features:
- State
- Median income
- Mean income
└── requirements.txt