"""
Time Series Forecasting module.

Uses ARIMA with BIC-based order selection to forecast Malaysia's national
overall CPI inflation (year-on-year, monthly).

Data source : data/processed/overall_inflation.csv
Test set    : last 24 months
Forecast    : 24 months beyond the latest observation
"""

import os
import warnings
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "figures")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "models")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

TEST_MONTHS = 24
FORECAST_HORIZON = 24


def check_stationarity(series: pd.Series) -> dict:
    result = adfuller(series.dropna())
    return {
        "adf_stat": round(result[0], 4),
        "p_value": round(result[1], 4),
        "is_stationary": result[1] < 0.05,
    }


def select_order(series: pd.Series, p_max: int = 4, q_max: int = 4) -> tuple:
    """
    BIC grid search over p in [0, p_max] and q in [0, q_max].
    d is determined by ADF test. BIC penalises complexity more than AIC,
    yielding more parsimonious models that generalise better.
    """
    stat = check_stationarity(series)
    d = 0 if stat["is_stationary"] else 1

    best_bic = np.inf
    best_order = (1, d, 1)

    for p in range(0, p_max + 1):
        for q in range(0, q_max + 1):
            if p == 0 and q == 0:
                continue
            try:
                m = ARIMA(series.values, order=(p, d, q)).fit()
                if m.bic < best_bic:
                    best_bic = m.bic
                    best_order = (p, d, q)
            except Exception:
                pass

    return best_order


def fit_arima(series: pd.Series, order: tuple):
    return ARIMA(series.values, order=order).fit()


def _extract_forecast(fc):
    mean = np.asarray(fc.predicted_mean)
    ci = np.asarray(fc.conf_int(alpha=0.05))
    return mean, ci[:, 0], ci[:, 1]


def train_test_split_ts(series: pd.Series, test_n: int = TEST_MONTHS):
    return series.iloc[:-test_n], series.iloc[-test_n:]


def evaluate_forecast(actual: pd.Series, predicted: np.ndarray) -> dict:
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual.values - predicted) / (np.abs(actual.values) + 1e-8))) * 100
    return {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 2)}


def compute_fuel_correlation(inflation_df: pd.DataFrame, fuelprice_df: pd.DataFrame) -> dict:
    """
    Merge monthly CPI inflation with monthly fuel prices and compute
    Pearson correlations for each fuel type. Also includes lag-1 correlation
    to check if fuel prices lead inflation by one month.
    """
    merged = pd.merge(
        inflation_df[["date", "inflation_yoy"]],
        fuelprice_df[["date", "ron95", "ron97", "diesel", "avg_fuel"]],
        on="date",
        how="inner",
    ).dropna()

    corr = {}
    for col in ["ron95", "ron97", "diesel", "avg_fuel"]:
        r = merged["inflation_yoy"].corr(merged[col])
        r_lag1 = merged["inflation_yoy"].iloc[1:].corr(merged[col].iloc[:-1])
        corr[col] = {"contemporaneous": round(r, 4), "lag1": round(r_lag1, 4)}

    return {
        "correlations": corr,
        "n_overlap_months": len(merged),
        "overlap_start": str(merged["date"].min().date()),
        "overlap_end": str(merged["date"].max().date()),
        "merged_data": merged.to_dict(orient="records"),
    }


def run_live(inflation_df: pd.DataFrame, horizon: int = FORECAST_HORIZON, order: tuple = None):
    """
    Generator for SSE streaming. Yields progress and result dicts.
    Each dict has a 'type' key: 'progress' | 'result' | 'error'.
    """
    series = inflation_df.set_index("date")["inflation_yoy"].sort_index()

    if len(series) < 30:
        yield {"type": "error", "message": "Not enough data (need ≥30 months)"}
        return

    train, test = train_test_split_ts(series)

    yield {"type": "progress", "step": "Running ADF stationarity test…", "pct": 10}
    stat = check_stationarity(train)
    stat_label = "stationary" if stat["is_stationary"] else "non-stationary"
    yield {"type": "progress", "step": f"ADF p={stat['p_value']} ({stat_label})", "pct": 22}

    if order is None:
        yield {"type": "progress", "step": "Selecting best ARIMA order via BIC grid search…", "pct": 38}
        order = select_order(train)

    yield {"type": "progress", "step": f"Fitting ARIMA{order} on training data…", "pct": 54}
    try:
        fitted = fit_arima(train, order)
    except Exception as exc:
        yield {"type": "error", "message": f"ARIMA fit failed: {exc}"}
        return

    yield {"type": "progress", "step": "Evaluating on held-out 24-month test period…", "pct": 68}
    test_pred, _, _ = _extract_forecast(fitted.get_forecast(steps=len(test)))
    metrics = evaluate_forecast(test, test_pred)
    yield {"type": "progress",
           "step": f"RMSE={metrics['RMSE']}  MAPE={metrics['MAPE']}%", "pct": 82}

    yield {"type": "progress", "step": f"Refitting on full series → forecasting {horizon} months…", "pct": 93}
    final_model = fit_arima(series, order)
    future_pred, future_lower, future_upper = _extract_forecast(
        final_model.get_forecast(steps=horizon)
    )
    last_date = series.index.max()
    future_dates = pd.date_range(last_date, periods=horizon + 1, freq="MS")[1:]

    yield {
        "type": "result",
        "pct": 100,
        "data": {
            "train": {
                "dates": [str(d.date()) for d in train.index],
                "values": [float(v) for v in train.values],
            },
            "test": {
                "dates":     [str(d.date()) for d in test.index],
                "actual":    [float(v) for v in test.values],
                "predicted": [float(v) for v in test_pred],
            },
            "forecast": {
                "dates":  [str(d.date()) for d in future_dates],
                "values": [float(v) for v in future_pred],
                "lower":  [float(v) for v in future_lower],
                "upper":  [float(v) for v in future_upper],
            },
            "metrics": {k: float(v) for k, v in metrics.items()},
            "stationarity": {
                "adf_stat":      float(stat["adf_stat"]),
                "p_value":       float(stat["p_value"]),
                "is_stationary": bool(stat["is_stationary"]),
            },
            "arima_order": list(order),
            "aic": round(float(final_model.aic), 2),
            "bic": round(float(final_model.bic), 2),
            "horizon": horizon,
        },
    }


def plot_forecast(result: dict, save_path: str = None):
    order_str = "ARIMA({},{},{})".format(*result["arima_order"])
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    fig.suptitle(
        f"Malaysian CPI Inflation Forecast — {order_str}  "
        f"[AIC={result.get('aic', '?')}, BIC={result.get('bic', '?')}]",
        fontsize=13, fontweight="bold",
    )

    ax = axes[0]
    # Show only last 10 years of history for readability
    train_dates = pd.to_datetime(result["train"]["dates"])
    train_vals = result["train"]["values"]
    cutoff = train_dates.max() - pd.DateOffset(years=10)
    mask = train_dates >= cutoff
    ax.plot(train_dates[mask], np.array(train_vals)[mask], "b-", linewidth=1.2, label="Historical")
    ax.plot(pd.to_datetime(result["test"]["dates"]), result["test"]["actual"],
            "g-o", markersize=3, label="Actual (test)")
    ax.plot(pd.to_datetime(result["test"]["dates"]), result["test"]["predicted"],
            "r--o", markersize=3, label="Predicted (test)")
    forecast_dates = pd.to_datetime(result["forecast"]["dates"])
    ax.plot(forecast_dates, result["forecast"]["values"], "m-^", markersize=4,
            label=f"Forecast ({len(forecast_dates)}m)")
    ax.fill_between(
        forecast_dates,
        result["forecast"]["lower"],
        result["forecast"]["upper"],
        color="violet", alpha=0.25, label="95% CI",
    )
    ax.axhline(y=0, color="black", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.axvline(x=pd.to_datetime(result["test"]["dates"][0]),
               color="gray", linestyle=":", alpha=0.5)
    ax.set_xlabel("Date")
    ax.set_ylabel("Inflation YoY (%)")
    ax.set_title("Historical + 24-Month Forecast")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    ax2 = axes[1]
    ax2.plot(pd.to_datetime(result["test"]["dates"]), result["test"]["actual"],
             "g-o", markersize=4, label="Actual")
    ax2.plot(pd.to_datetime(result["test"]["dates"]), result["test"]["predicted"],
             "r--o", markersize=4, label="Predicted")
    m = result["metrics"]
    ax2.set_title(f"Test Period Evaluation (24 months)\nMAE={m['MAE']} | RMSE={m['RMSE']} | MAPE={m['MAPE']}%")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Inflation YoY (%)")
    ax2.axhline(y=0, color="black", linestyle=":", linewidth=0.8, alpha=0.5)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax2.get_xticklabels(), rotation=30, ha="right")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_division_trends(cpi_inflation_df: pd.DataFrame, save_path: str = None):
    """Line chart of yoy inflation by division for recent 5 years."""
    cutoff = cpi_inflation_df["date"].max() - pd.DateOffset(years=5)
    recent = cpi_inflation_df[cpi_inflation_df["date"] >= cutoff].dropna(subset=["inflation_yoy"])
    divisions = [d for d in recent["division"].unique() if d != "overall"]

    import seaborn as sns
    palette = sns.color_palette("tab20", len(divisions))
    fig, ax = plt.subplots(figsize=(14, 7))
    for i, div in enumerate(sorted(divisions)):
        grp = recent[recent["division"] == div].sort_values("date")
        label = grp["division_label"].iloc[0] if "division_label" in grp.columns else div
        ax.plot(grp["date"], grp["inflation_yoy"], linewidth=1.4,
                label=label, color=palette[i])

    overall = recent[recent["division"] == "overall"].sort_values("date")
    ax.plot(overall["date"], overall["inflation_yoy"], "k-", linewidth=2.5,
            label="Overall CPI", zorder=5)
    ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Year-on-Year Inflation (%)", fontsize=11)
    ax.set_title("CPI Inflation by Division — Last 5 Years", fontsize=13, fontweight="bold")
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def run_all(inflation_df: pd.DataFrame = None, fuelprice_df: pd.DataFrame = None) -> dict:
    if inflation_df is None:
        inflation_df = pd.read_csv(os.path.join(PROCESSED_DIR, "overall_inflation.csv"),
                                   parse_dates=["date"])
    if fuelprice_df is None:
        fp_path = os.path.join(PROCESSED_DIR, "fuelprice_clean.csv")
        if os.path.exists(fp_path):
            fuelprice_df = pd.read_csv(fp_path, parse_dates=["date"])

    print("Running ARIMA forecasting on national CPI inflation...")
    series = inflation_df.set_index("date")["inflation_yoy"].sort_index()
    train, test = train_test_split_ts(series)

    stationarity = check_stationarity(train)
    print(f"  ADF test: p={stationarity['p_value']} "
          f"({'stationary' if stationarity['is_stationary'] else 'non-stationary'})")

    order = select_order(train)
    print(f"  BIC-selected order: ARIMA{order}")

    fitted = fit_arima(train, order)
    test_pred, _, _ = _extract_forecast(fitted.get_forecast(steps=len(test)))
    metrics = evaluate_forecast(test, test_pred)
    print(f"  Test metrics: MAE={metrics['MAE']} RMSE={metrics['RMSE']} MAPE={metrics['MAPE']}%")

    final_model = fit_arima(series, order)
    future_pred, future_lower, future_upper = _extract_forecast(
        final_model.get_forecast(steps=FORECAST_HORIZON)
    )
    last_date = series.index.max()
    future_dates = pd.date_range(last_date, periods=FORECAST_HORIZON + 1, freq="MS")[1:]

    result = {
        "train": {
            "dates":  [str(d.date()) for d in train.index],
            "values": [float(v) for v in train.values],
        },
        "test": {
            "dates":     [str(d.date()) for d in test.index],
            "actual":    [float(v) for v in test.values],
            "predicted": [float(v) for v in test_pred],
        },
        "forecast": {
            "dates":  [str(d.date()) for d in future_dates],
            "values": [float(v) for v in future_pred],
            "lower":  [float(v) for v in future_lower],
            "upper":  [float(v) for v in future_upper],
        },
        "metrics": {k: float(v) for k, v in metrics.items()},
        "stationarity": {
            "adf_stat":      float(stationarity["adf_stat"]),
            "p_value":       float(stationarity["p_value"]),
            "is_stationary": bool(stationarity["is_stationary"]),
        },
        "arima_order": list(order),
        "aic": round(float(final_model.aic), 2),
        "bic": round(float(final_model.bic), 2),
        "horizon": FORECAST_HORIZON,
        "series_length": len(series),
        "test_months": TEST_MONTHS,
    }

    # Fuel price correlation (if available)
    if fuelprice_df is not None:
        print("  Computing fuel price correlation...")
        result["fuel_correlation"] = compute_fuel_correlation(inflation_df, fuelprice_df)

    with open(os.path.join(MODELS_DIR, "arima_results.json"), "w") as f:
        json.dump({k: v for k, v in result.items() if k != "fuel_correlation"
                   or not isinstance(v.get("merged_data"), list)}, f, indent=2, default=str)

    # Save full result including merged data separately
    with open(os.path.join(MODELS_DIR, "arima_results.json"), "w") as f:
        out = {k: v for k, v in result.items() if k != "fuel_correlation"}
        json.dump(out, f, indent=2, default=str)

    if "fuel_correlation" in result:
        with open(os.path.join(MODELS_DIR, "fuel_correlation.json"), "w") as f:
            json.dump(result["fuel_correlation"], f, indent=2, default=str)

    plot_forecast(result, save_path=os.path.join(FIGURES_DIR, "ts_forecast.png"))

    # Load full cpi_inflation for division trends plot
    cpi_path = os.path.join(PROCESSED_DIR, "cpi_inflation_clean.csv")
    if os.path.exists(cpi_path):
        cpi_all = pd.read_csv(cpi_path, parse_dates=["date"])
        plot_division_trends(cpi_all, save_path=os.path.join(FIGURES_DIR, "ts_division_trends.png"))

    print("  Figures saved to outputs/figures/")
    return result


if __name__ == "__main__":
    run_all()
