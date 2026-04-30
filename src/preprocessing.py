"""
Preprocessing module: loads, cleans, and merges all 4 DOSM datasets.
Outputs cleaned DataFrames and saves processed CSVs to data/processed/.
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


def load_hies_district() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(RAW_DIR, "hies_district.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    numeric_cols = ["income_mean", "income_median", "expenditure_mean", "gini", "poverty"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df["savings_rate"] = (df["income_mean"] - df["expenditure_mean"]) / df["income_mean"] * 100
    df["income_expenditure_ratio"] = df["income_mean"] / df["expenditure_mean"]
    df = df.dropna(subset=numeric_cols)
    return df


def load_hies_state() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(RAW_DIR, "hies_state.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    numeric_cols = ["income_mean", "income_median", "expenditure_mean", "gini", "poverty"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=numeric_cols)
    return df


def load_poverty_district() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(RAW_DIR, "hh_poverty_district.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["poverty_absolute"] = pd.to_numeric(df["poverty_absolute"], errors="coerce")
    df["poverty_relative"] = pd.to_numeric(df["poverty_relative"], errors="coerce")
    df = df.dropna(subset=["poverty_absolute", "poverty_relative"])
    # Pivot to wide format: one row per district with 2019 and 2022 columns
    pivot = df.pivot_table(
        index=["state", "district"],
        columns="year",
        values=["poverty_absolute", "poverty_relative"],
    ).reset_index()
    pivot.columns = [
        "state", "district",
        "poverty_abs_2019", "poverty_abs_2022",
        "poverty_rel_2019", "poverty_rel_2022",
    ]
    pivot["poverty_abs_change"] = pivot["poverty_abs_2022"] - pivot["poverty_abs_2019"]
    pivot["poverty_rel_change"] = pivot["poverty_rel_2022"] - pivot["poverty_rel_2019"]
    return df, pivot


def load_gini_state() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(RAW_DIR, "hh_inequality_state.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["gini"] = pd.to_numeric(df["gini"], errors="coerce")
    df = df.dropna(subset=["gini"]).sort_values(["state", "year"]).reset_index(drop=True)
    return df


def interpolate_gini_annual(gini_df: pd.DataFrame) -> pd.DataFrame:
    """
    Interpolate Gini series to uniform annual frequency per state.
    Required for ARIMA which expects evenly-spaced time steps.
    """
    records = []
    for state, grp in gini_df.groupby("state"):
        grp = grp.set_index("year")["gini"]
        # Fill in every year from min to max
        full_index = range(grp.index.min(), grp.index.max() + 1)
        grp = grp.reindex(full_index).interpolate(method="linear")
        for yr, val in grp.items():
            records.append({"state": state, "year": yr, "gini": val})
    return pd.DataFrame(records)


def build_district_features(hies_df: pd.DataFrame) -> pd.DataFrame:
    """Return feature matrix used for clustering."""
    features = [
        "income_mean", "income_median", "expenditure_mean",
        "gini", "poverty", "savings_rate", "income_expenditure_ratio"
    ]
    df = hies_df[["state", "district"] + features].copy()
    return df


def run_all():
    print("Loading and preprocessing datasets...")

    hies_district = load_hies_district()
    hies_district.to_csv(os.path.join(PROCESSED_DIR, "hies_district_clean.csv"), index=False)
    print(f"  hies_district: {len(hies_district)} rows")

    hies_state = load_hies_state()
    hies_state.to_csv(os.path.join(PROCESSED_DIR, "hies_state_clean.csv"), index=False)
    print(f"  hies_state: {len(hies_state)} rows")

    poverty_long, poverty_wide = load_poverty_district()
    poverty_long.to_csv(os.path.join(PROCESSED_DIR, "poverty_district_long.csv"), index=False)
    poverty_wide.to_csv(os.path.join(PROCESSED_DIR, "poverty_district_wide.csv"), index=False)
    print(f"  poverty_district: {len(poverty_wide)} districts (wide)")

    gini_state = load_gini_state()
    gini_annual = interpolate_gini_annual(gini_state)
    gini_state.to_csv(os.path.join(PROCESSED_DIR, "gini_state_clean.csv"), index=False)
    gini_annual.to_csv(os.path.join(PROCESSED_DIR, "gini_state_annual.csv"), index=False)
    print(f"  gini_state: {len(gini_state)} records -> {len(gini_annual)} after annual interpolation")

    print("Preprocessing complete. Files saved to data/processed/")
    return hies_district, hies_state, poverty_long, poverty_wide, gini_state, gini_annual


if __name__ == "__main__":
    run_all()
