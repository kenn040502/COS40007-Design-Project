"""Compute exact statistics used in the report from regenerated processed data."""
import os, json
import pandas as pd

PROC = os.path.join(os.path.dirname(__file__), "data", "processed")
MODELS = os.path.join(os.path.dirname(__file__), "outputs", "models")

km = pd.read_csv(os.path.join(PROC, "districts_kmeans_clustered.csv"))
pov = pd.read_csv(os.path.join(PROC, "poverty_district_wide.csv"))
gini_annual = pd.read_csv(os.path.join(PROC, "gini_state_annual.csv"))
gini_clean = pd.read_csv(os.path.join(PROC, "gini_state_clean.csv"))
hies_d = pd.read_csv(os.path.join(PROC, "hies_district_clean.csv"))

print("===== CLUSTER PROFILE (K-Means) =====")
prof = km.groupby("cluster_label").agg(
    districts=("district", "count"),
    income_mean=("income_mean", "mean"),
    income_median=("income_median", "mean"),
    expenditure_mean=("expenditure_mean", "mean"),
    gini=("gini", "mean"),
    poverty=("poverty", "mean"),
).round(2)
prof["pct"] = (prof["districts"] / prof["districts"].sum() * 100).round(1)
print(prof.to_string())

print("\n===== CLUSTER MEMBERSHIP BY STATE (low-income cluster) =====")
low_label = prof["income_mean"].idxmin()
print("Low-income cluster label:", low_label)
low = km[km["cluster_label"] == low_label]
print(low["state"].value_counts().to_string())

print("\n===== POVERTY CHANGE 2019->2022: TOP 5 INCREASES =====")
inc = pov.sort_values("poverty_abs_change", ascending=False).head(5)
print(inc[["state","district","poverty_abs_2019","poverty_abs_2022","poverty_abs_change"]].to_string(index=False))
print("\n===== TOP 5 DECREASES =====")
dec = pov.sort_values("poverty_abs_change").head(5)
print(dec[["state","district","poverty_abs_2019","poverty_abs_2022","poverty_abs_change"]].to_string(index=False))

print("\n===== NATIONAL GINI (unweighted mean of states) =====")
nat = gini_clean.groupby("year")["gini"].mean()
for y in [1974, 1976, 1989, 1997, 2009, 2016, 2019, 2022]:
    if y in nat.index:
        print(f"  {y}: {nat.loc[y]:.4f}")
print(f"  earliest {nat.index.min()}: {nat.iloc[0]:.4f}, latest {nat.index.max()}: {nat.iloc[-1]:.4f}")

print("\n===== ARIMA forecast 2030 national mean (state-mean of forecasts) =====")
with open(os.path.join(MODELS, "arima_results.json")) as f:
    ar = json.load(f)
f2030 = [r["forecast_gini"][-1] for r in ar.values() if "error" not in r]
print(f"  mean forecast 2030 = {sum(f2030)/len(f2030):.4f}  across {len(f2030)} states")

print("\n===== HIES district extremes =====")
print("Lowest mean income district:", hies_d.loc[hies_d['income_mean'].idxmin(), ['state','district','income_mean','poverty']].to_dict())
print("Highest poverty district:", hies_d.loc[hies_d['poverty'].idxmax(), ['state','district','income_mean','poverty']].to_dict())
print("N districts:", len(hies_d), "| N states covered:", hies_d['state'].nunique())
print("Mean district income (all):", round(hies_d['income_mean'].mean(),0), "| Median poverty:", round(hies_d['poverty'].median(),2))

print("\n===== PCA variance =====")
print(open(os.path.join(MODELS, "clustering_results.json")).read()[:50], "...(see json)")
