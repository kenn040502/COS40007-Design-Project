"""
Preprocessing module: loads, cleans, and merges all 4 DOSM datasets.

Datasets:
  cpi_2d_inflation.csv  - Monthly national CPI inflation by division (1980-present)
  cpi_2d_state.csv      - Monthly CPI index by state and division (2010-present)
  fuelprice.csv         - Weekly retail fuel prices (2017-present)
  hh_income_state.csv   - Survey-based household income by state (1970-2022)

Outputs saved to data/processed/.
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

DIVISION_LABELS = {
    "01": "Food & Non-Alcoholic Beverages",
    "02": "Alcoholic Beverages & Tobacco",
    "03": "Clothing & Footwear",
    "04": "Housing, Water, Electricity & Gas",
    "05": "Furnishings & Household Equipment",
    "06": "Health",
    "07": "Transport",
    "08": "Information & Communication",
    "09": "Recreation, Sport & Culture",
    "10": "Education",
    "11": "Restaurants & Accommodation",
    "12": "Insurance & Financial Services",
    "13": "Personal Care & Miscellaneous",
    "overall": "Overall CPI",
}


def load_cpi_inflation() -> pd.DataFrame:
    """National monthly CPI inflation by division."""
    df = pd.read_csv(os.path.join(RAW_DIR, "cpi_2d_inflation.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["inflation_yoy"] = pd.to_numeric(df["inflation_yoy"], errors="coerce")
    df["inflation_mom"] = pd.to_numeric(df["inflation_mom"], errors="coerce")
    df["division_label"] = df["division"].map(DIVISION_LABELS).fillna(df["division"])
    df = df.sort_values(["division", "date"]).reset_index(drop=True)
    return df


def load_cpi_state() -> pd.DataFrame:
    """Monthly CPI index by state and division."""
    df = pd.read_csv(os.path.join(RAW_DIR, "cpi_2d_state.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["index"] = pd.to_numeric(df["index"], errors="coerce")
    df["division_label"] = df["division"].map(DIVISION_LABELS).fillna(df["division"])
    df = df.dropna(subset=["index"])
    df = df.sort_values(["state", "division", "date"]).reset_index(drop=True)
    return df


def load_fuelprice() -> pd.DataFrame:
    """
    Weekly retail fuel prices filtered to 'level' series.
    Resampled to monthly mean to align with CPI frequency.
    """
    df = pd.read_csv(os.path.join(RAW_DIR, "fuelprice.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["series_type"] == "level"].copy()
    for col in ["ron95", "ron97", "diesel"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[["date", "ron95", "ron97", "diesel"]].dropna(subset=["ron95", "ron97", "diesel"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df.set_index("date").resample("MS").mean().reset_index()
    df["avg_fuel"] = df[["ron95", "ron97", "diesel"]].mean(axis=1)
    return df


def load_income_state() -> pd.DataFrame:
    """Survey-based household income by state."""
    df = pd.read_csv(os.path.join(RAW_DIR, "hh_income_state.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["income_mean"] = pd.to_numeric(df["income_mean"], errors="coerce")
    df["income_median"] = pd.to_numeric(df["income_median"], errors="coerce")
    df = df.dropna(subset=["income_mean"]).sort_values(["state", "year"]).reset_index(drop=True)
    return df


def build_overall_inflation(cpi_inflation: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the national 'overall' division time series for ARIMA forecasting.
    Drops leading rows where yoy is NaN (no prior-year reference before 1981).
    """
    df = cpi_inflation[cpi_inflation["division"] == "overall"].copy()
    df = df.dropna(subset=["inflation_yoy"]).reset_index(drop=True)
    return df


def build_state_features(cpi_state: pd.DataFrame, income_state: pd.DataFrame) -> pd.DataFrame:
    """
    Build one row per state with features suitable for clustering:
      mean_cpi_index       : average 'overall' CPI index across all months
      cpi_growth_rate      : % change from earliest to latest overall CPI per state
      cpi_volatility       : std dev of monthly overall CPI (price stability proxy)
      income_mean_latest   : most recent survey mean income per state
      income_median_latest : most recent survey median income per state
    """
    overall = cpi_state[cpi_state["division"] == "overall"].copy()

    agg = overall.groupby("state")["index"].agg(
        mean_cpi_index="mean",
        cpi_volatility="std",
    )

    def pct_growth(grp):
        grp = grp.sort_values("date")
        if len(grp) < 2:
            return np.nan
        first, last = grp["index"].iloc[0], grp["index"].iloc[-1]
        return (last - first) / first * 100

    cpi_growth = overall.groupby("state").apply(pct_growth).rename("cpi_growth_rate")

    latest_income = (
        income_state.sort_values("year")
        .groupby("state")
        .last()[["income_mean", "income_median"]]
        .rename(columns={
            "income_mean": "income_mean_latest",
            "income_median": "income_median_latest",
        })
    )

    features = pd.concat([agg, cpi_growth, latest_income], axis=1).reset_index()
    features = features.dropna()
    return features


def run_all():
    print("Loading and preprocessing datasets...")

    cpi_inflation = load_cpi_inflation()
    cpi_inflation.to_csv(os.path.join(PROCESSED_DIR, "cpi_inflation_clean.csv"), index=False)
    print(f"  cpi_inflation  : {len(cpi_inflation)} rows, {cpi_inflation['division'].nunique()} divisions")

    cpi_state = load_cpi_state()
    cpi_state.to_csv(os.path.join(PROCESSED_DIR, "cpi_state_clean.csv"), index=False)
    print(f"  cpi_state      : {len(cpi_state)} rows, {cpi_state['state'].nunique()} states")

    fuelprice = load_fuelprice()
    fuelprice.to_csv(os.path.join(PROCESSED_DIR, "fuelprice_clean.csv"), index=False)
    print(f"  fuelprice      : {len(fuelprice)} monthly records ({fuelprice['date'].min().year}-{fuelprice['date'].max().year})")

    income_state = load_income_state()
    income_state.to_csv(os.path.join(PROCESSED_DIR, "income_state_clean.csv"), index=False)
    print(f"  income_state   : {len(income_state)} rows, {income_state['state'].nunique()} states")

    overall_inflation = build_overall_inflation(cpi_inflation)
    overall_inflation.to_csv(os.path.join(PROCESSED_DIR, "overall_inflation.csv"), index=False)
    print(f"  overall_inflation: {len(overall_inflation)} monthly records "
          f"({overall_inflation['date'].min().year}-{overall_inflation['date'].max().year})")

    state_features = build_state_features(cpi_state, income_state)
    state_features.to_csv(os.path.join(PROCESSED_DIR, "state_features.csv"), index=False)
    n_feat = len(state_features.columns) - 1
    print(f"  state_features : {len(state_features)} states x {n_feat} features")

    print("Preprocessing complete. Files saved to data/processed/")
    return cpi_inflation, cpi_state, fuelprice, income_state, overall_inflation, state_features


if __name__ == "__main__":
    run_all()
