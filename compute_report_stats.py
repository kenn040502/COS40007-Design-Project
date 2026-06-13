"""Compute exact statistics used in the report from regenerated processed data.
Run AFTER run_analysis.py has populated data/processed/ and outputs/models/.
"""
import os
import json
import pandas as pd

PROC = os.path.join(os.path.dirname(__file__), "data", "processed")
MODELS = os.path.join(os.path.dirname(__file__), "outputs", "models")


def load(filename, **kwargs):
    return pd.read_csv(os.path.join(PROC, filename), **kwargs)


km = load("states_kmeans_clustered.csv")
hc = load("states_hierarchical_clustered.csv")
state_features = load("state_features.csv")
income = load("income_state_clean.csv", parse_dates=["date"])
overall_inf = load("overall_inflation.csv", parse_dates=["date"])
cpi_state = load("cpi_state_clean.csv", parse_dates=["date"])

print("===== CLUSTER PROFILE (K-Means) =====")
prof = km.groupby("cluster_label").agg(
    states=("state", "count"),
    mean_cpi_index=("mean_cpi_index", "mean"),
    cpi_growth_rate=("cpi_growth_rate", "mean"),
    cpi_volatility=("cpi_volatility", "mean"),
    income_mean=("income_mean_latest", "mean"),
    income_median=("income_median_latest", "mean"),
).round(2)
prof["pct"] = (prof["states"] / prof["states"].sum() * 100).round(1)
print(prof.to_string())

print("\n===== STATE CLUSTER MEMBERSHIP =====")
print(km[["state", "cluster_label"]].sort_values("cluster_label").to_string(index=False))

print("\n===== INCOME EXTREMES BY STATE (latest survey) =====")
latest = income.sort_values("date").groupby("state").last().reset_index()
print("Highest mean income:")
print(latest.nlargest(5, "income_mean")[["state", "income_mean", "income_median"]].to_string(index=False))
print("Lowest mean income:")
print(latest.nsmallest(5, "income_mean")[["state", "income_mean", "income_median"]].to_string(index=False))

print("\n===== OVERALL CPI INFLATION (national) =====")
recent = overall_inf.sort_values("date").tail(12)
print(f"  Latest date : {overall_inf['date'].max().strftime('%Y-%m')}")
print(f"  Latest YoY  : {overall_inf.sort_values('date')['inflation_yoy'].iloc[-1]:.2f}%")
print(f"  Max YoY     : {overall_inf['inflation_yoy'].max():.2f}%  ({overall_inf.loc[overall_inf['inflation_yoy'].idxmax(), 'date'].strftime('%Y-%m')})")
print(f"  Min YoY     : {overall_inf['inflation_yoy'].min():.2f}%  ({overall_inf.loc[overall_inf['inflation_yoy'].idxmin(), 'date'].strftime('%Y-%m')})")

print("\n===== ARIMA RESULTS =====")
with open(os.path.join(MODELS, "arima_results.json")) as f:
    ar = json.load(f)
print(f"  ARIMA order : {ar['arima_order']}")
print(f"  AIC         : {ar.get('aic', 'n/a')}")
print(f"  BIC         : {ar.get('bic', 'n/a')}")
m = ar["metrics"]
print(f"  Test MAE    : {m['MAE']:.4f}")
print(f"  Test RMSE   : {m['RMSE']:.4f}")
print(f"  Test MAPE   : {m['MAPE']:.2f}%")
fc = ar["forecast"]["values"]
print(f"  Forecast horizon : {ar['horizon']} months")
print(f"  Forecast range   : {min(fc):.2f}% – {max(fc):.2f}%")

print("\n===== CLUSTERING VALIDITY SCORES =====")
with open(os.path.join(MODELS, "clustering_results.json")) as f:
    cr = json.load(f)
print(f"  Best k (silhouette) : {cr['best_k']}")
for method in ("kmeans", "hierarchical"):
    s = cr[method]["scores"]
    print(f"  {method:15s}: silhouette={s['silhouette']}  "
          f"davies_bouldin={s['davies_bouldin']}  "
          f"calinski_harabasz={s['calinski_harabasz']}")

print("\n===== STATE CPI GROWTH RATES =====")
overall = cpi_state[cpi_state["division"] == "overall"].copy()
growth = (
    overall.sort_values("date")
    .groupby("state")
    .apply(lambda g: round((g["index"].iloc[-1] - g["index"].iloc[0]) / g["index"].iloc[0] * 100, 2))
    .reset_index()
)
growth.columns = ["state", "cpi_growth_pct"]
print(growth.sort_values("cpi_growth_pct", ascending=False).to_string(index=False))
