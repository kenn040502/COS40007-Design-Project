"""
Time Series Forecasting module.
Uses ARIMA to model and forecast Gini coefficient trends per Malaysian state.
Train/test split: last 5 years as test. Forecast horizon: 2023-2030.
"""

import os
import warnings
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "figures")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "models")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

FORECAST_HORIZON = 8  # years beyond 2022
ARIMA_ORDER = (2, 1, 2)  # (p, d, q)
TEST_YEARS = 5


def check_stationarity(series: pd.Series) -> dict:
    result = adfuller(series.dropna())
    return {
        "adf_stat": round(result[0], 4),
        "p_value": round(result[1], 4),
        "is_stationary": result[1] < 0.05,
    }


def fit_arima(series: pd.Series, order=ARIMA_ORDER):
    model = ARIMA(series, order=order)
    return model.fit()


def train_test_split_ts(series: pd.Series, test_n=TEST_YEARS):
    return series.iloc[:-test_n], series.iloc[-test_n:]


def evaluate_forecast(actual: pd.Series, predicted: np.ndarray) -> dict:
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual.values - predicted) / actual.values)) * 100
    return {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 2)}


def run_live(state: str, gini_annual_df: pd.DataFrame,
             horizon: int = FORECAST_HORIZON, order: tuple = ARIMA_ORDER):
    """
    Generator for SSE streaming. Yields progress and result dicts for one state.
    Each dict has a "type" key: "progress" | "result" | "error".
    """
    grp = gini_annual_df[gini_annual_df["state"] == state].set_index("year")["gini"].sort_index()

    if len(grp) < 10:
        yield {"type": "error", "message": f"Not enough data for {state} (need ≥10 observations)"}
        return

    yield {"type": "progress", "step": "Running ADF stationarity test…", "pct": 15}
    train, test = train_test_split_ts(grp)
    stat = check_stationarity(train)
    stat_label = "stationary" if stat["is_stationary"] else "non-stationary"
    yield {"type": "progress", "step": f"ADF p={stat['p_value']} ({stat_label})", "pct": 30}

    yield {"type": "progress", "step": f"Fitting ARIMA{order} on training data…", "pct": 46}
    try:
        fitted = fit_arima(train, order)
    except Exception as exc:
        yield {"type": "error", "message": f"ARIMA fit failed: {exc}"}
        return

    yield {"type": "progress", "step": "Evaluating on held-out test years…", "pct": 62}
    test_pred = fitted.forecast(steps=len(test))
    metrics = evaluate_forecast(test, test_pred)
    yield {"type": "progress",
           "step": f"RMSE={metrics['RMSE']}  MAPE={metrics['MAPE']}%", "pct": 78}

    end_year = int(grp.index.max()) + horizon
    yield {"type": "progress",
           "step": f"Refitting on full series → forecasting to {end_year}…", "pct": 91}
    final_model = fit_arima(grp, order)
    future_pred = final_model.forecast(steps=horizon)
    future_years = list(range(int(grp.index.max()) + 1, int(grp.index.max()) + horizon + 1))

    yield {
        "type": "result",
        "pct": 100,
        "data": {
            "train": {
                "years": list(map(int, train.index)),
                "gini":  [float(v) for v in train.values],
            },
            "test": {
                "years":     list(map(int, test.index)),
                "actual":    [float(v) for v in test.values],
                "predicted": [float(v) for v in test_pred],
            },
            "forecast": {
                "years": future_years,
                "gini":  [float(v) for v in future_pred],
            },
            "metrics": {k: float(v) for k, v in metrics.items()},
            "stationarity": {
                "adf_stat":     float(stat["adf_stat"]),
                "p_value":      float(stat["p_value"]),
                "is_stationary": bool(stat["is_stationary"]),
            },
            "arima_order": list(order),
            "horizon": horizon,
        },
    }


def run_forecast_all_states(gini_annual_df: pd.DataFrame) -> dict:
    """
    Fit ARIMA per state. Returns dict of results keyed by state name.
    """
    results = {}
    states = gini_annual_df["state"].unique()

    for state in states:
        grp = gini_annual_df[gini_annual_df["state"] == state].set_index("year")["gini"]
        grp = grp.sort_index()

        if len(grp) < 10:
            continue  # not enough data

        train, test = train_test_split_ts(grp)
        stationarity = check_stationarity(train)

        try:
            fitted = fit_arima(train)
            # In-sample forecast on test set
            test_pred = fitted.forecast(steps=len(test))
            metrics = evaluate_forecast(test, test_pred)

            # Refit on full series for final forecast
            final_model = fit_arima(grp)
            future_pred = final_model.forecast(steps=FORECAST_HORIZON)
            future_years = list(range(grp.index.max() + 1, grp.index.max() + FORECAST_HORIZON + 1))

            results[state] = {
                "train_years": list(map(int, train.index)),
                "train_gini": [float(v) for v in train.values],
                "test_years": list(map(int, test.index)),
                "test_gini": [float(v) for v in test.values],
                "test_pred": [float(v) for v in test_pred],
                "forecast_years": future_years,
                "forecast_gini": [float(v) for v in future_pred],
                "metrics": {k: float(v) for k, v in metrics.items()},
                "stationarity": {
                    "adf_stat": float(stationarity["adf_stat"]),
                    "p_value": float(stationarity["p_value"]),
                    "is_stationary": bool(stationarity["is_stationary"]),
                },
                "arima_order": list(ARIMA_ORDER),
            }
        except Exception as e:
            results[state] = {"error": str(e)}

    # Save results
    with open(os.path.join(MODELS_DIR, "arima_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    return results


def plot_forecast(state: str, result: dict, save_path: str = None):
    if "error" in result:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"Gini Coefficient Forecast — {state}", fontsize=14, fontweight="bold")

    # Left: full history + forecast
    ax = axes[0]
    ax.plot(result["train_years"], result["train_gini"], "b-o", markersize=4, label="Train")
    ax.plot(result["test_years"], result["test_gini"], "g-o", markersize=4, label="Test (actual)")
    ax.plot(result["test_years"], result["test_pred"], "r--o", markersize=4, label="Test (predicted)")
    ax.plot(result["forecast_years"], result["forecast_gini"], "m-^", markersize=5, label="Forecast 2023–2030")
    ax.axvline(x=result["test_years"][0], color="gray", linestyle=":", alpha=0.6, label="Train/test split")
    ax.set_xlabel("Year")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("Historical + Forecast")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Right: test period zoom with metrics
    ax2 = axes[1]
    ax2.plot(result["test_years"], result["test_gini"], "g-o", label="Actual")
    ax2.plot(result["test_years"], result["test_pred"], "r--o", label="Predicted")
    m = result["metrics"]
    ax2.set_title(
        f"Test Period Evaluation\nMAE={m['MAE']} | RMSE={m['RMSE']} | MAPE={m['MAPE']}%"
    )
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Gini Coefficient")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_all_states_summary(results: dict, save_path: str = None):
    """Bar chart comparing RMSE and 2030 forecast across states."""
    valid = {s: r for s, r in results.items() if "error" not in r}
    states = list(valid.keys())
    rmse = [r["metrics"]["RMSE"] for r in valid.values()]
    forecast_2030 = [r["forecast_gini"][-1] for r in valid.values()]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Gini Forecasting Summary — All States (ARIMA)", fontsize=13, fontweight="bold")

    # RMSE by state
    axes[0].barh(states, rmse, color="steelblue")
    axes[0].set_xlabel("RMSE")
    axes[0].set_title("Forecast Error (RMSE) by State")
    axes[0].axvline(x=np.mean(rmse), color="red", linestyle="--", label=f"Mean={np.mean(rmse):.4f}")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis="x")

    # Forecast 2030
    colors = ["#d73027" if v > 0.4 else "#fee090" if v > 0.35 else "#91cf60" for v in forecast_2030]
    axes[1].barh(states, forecast_2030, color=colors)
    axes[1].axvline(x=0.4, color="red", linestyle="--", label="Inequality threshold (0.40)")
    axes[1].set_xlabel("Gini Coefficient")
    axes[1].set_title("Forecasted Gini by 2030")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def run_all(gini_annual_df: pd.DataFrame = None) -> dict:
    if gini_annual_df is None:
        gini_annual_df = pd.read_csv(os.path.join(PROCESSED_DIR, "gini_state_annual.csv"))

    print("Running ARIMA forecasting per state...")
    results = run_forecast_all_states(gini_annual_df)

    success = sum(1 for r in results.values() if "error" not in r)
    print(f"  Forecast complete: {success}/{len(results)} states successful")

    # Save individual state plots
    for state, result in results.items():
        if "error" not in result:
            path = os.path.join(FIGURES_DIR, f"ts_{state.lower().replace(' ', '_')}.png")
            plot_forecast(state, result, save_path=path)

    # Summary plot
    plot_all_states_summary(
        results,
        save_path=os.path.join(FIGURES_DIR, "ts_summary_all_states.png")
    )
    print("  Figures saved to outputs/figures/")
    return results


if __name__ == "__main__":
    run_all()
