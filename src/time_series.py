"""
Time Series Forecasting module.
Uses ARIMA with per-state BIC-based order selection to model and forecast
Gini coefficient trends per Malaysian state.
Train/test split: last 5 years as test.
Metrics evaluated on real survey years only (not interpolated fill-ins).
Forecast horizon: 2023-2030.
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
TEST_YEARS = 5
# Short-series states get a restricted search space to avoid overfitting sparse data
SHORT_SERIES_THRESHOLD = 12   # real survey observations


def check_stationarity(series: pd.Series) -> dict:
    result = adfuller(series.dropna())
    return {
        "adf_stat": round(result[0], 4),
        "p_value": round(result[1], 4),
        "is_stationary": result[1] < 0.05,
    }


def select_order(series: pd.Series, p_max: int = 3, q_max: int = 3) -> tuple:
    """
    Per-series BIC grid search over p in [0,p_max] and q in [0,q_max].
    d is determined by ADF test. BIC penalises complexity more than AIC,
    yielding simpler, more generalizable models for short interpolated series.
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
    # Pass .values (plain ndarray) so statsmodels uses RangeIndex and get_forecast works
    return ARIMA(series.values, order=order).fit()


def _extract_forecast(fc):
    """Return (mean, lower_95, upper_95) as plain ndarrays from a ForecastResults object.
    Works whether the underlying index is RangeIndex (ndarray output) or DatetimeIndex."""
    mean = np.asarray(fc.predicted_mean)
    ci = np.asarray(fc.conf_int(alpha=0.05))
    return mean, ci[:, 0], ci[:, 1]


def train_test_split_ts(series: pd.Series, test_n=TEST_YEARS):
    return series.iloc[:-test_n], series.iloc[-test_n:]


def evaluate_forecast(actual: pd.Series, predicted: np.ndarray) -> dict:
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual.values - predicted) / actual.values)) * 100
    return {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 2)}


def evaluate_on_survey_years(
    test_series: pd.Series, test_pred: np.ndarray, survey_years: set
) -> dict:
    """
    Evaluate only on years that come from real DOSM surveys, not linear fill-ins.
    Falls back to full test set when no real years fall in the test window.
    """
    real_mask = test_series.index.isin(survey_years)
    if real_mask.sum() >= 2:
        return evaluate_forecast(test_series[real_mask], test_pred[real_mask])
    return evaluate_forecast(test_series, test_pred)


def run_live(state: str, gini_annual_df: pd.DataFrame,
             horizon: int = FORECAST_HORIZON, order: tuple = None):
    """
    Generator for SSE streaming. Yields progress and result dicts for one state.
    Each dict has a "type" key: "progress" | "result" | "error".
    """
    grp = gini_annual_df[gini_annual_df["state"] == state].set_index("year")["gini"].sort_index()

    if len(grp) < 10:
        yield {"type": "error", "message": f"Not enough data for {state} (need ≥10 observations)"}
        return

    yield {"type": "progress", "step": "Running ADF stationarity test…", "pct": 10}
    train, test = train_test_split_ts(grp)
    stat = check_stationarity(train)
    stat_label = "stationary" if stat["is_stationary"] else "non-stationary"
    yield {"type": "progress", "step": f"ADF p={stat['p_value']} ({stat_label})", "pct": 22}

    if order is None:
        yield {"type": "progress", "step": "Selecting best ARIMA order via BIC grid search…", "pct": 38}
        p_max = 1 if len(grp) < SHORT_SERIES_THRESHOLD else 3
        order = select_order(train, p_max=p_max, q_max=p_max)

    yield {"type": "progress", "step": f"Fitting ARIMA{order} on training data…", "pct": 54}
    try:
        fitted = fit_arima(train, order)
    except Exception as exc:
        yield {"type": "error", "message": f"ARIMA fit failed: {exc}"}
        return

    yield {"type": "progress", "step": "Evaluating on held-out test years…", "pct": 68}
    test_pred, _, _ = _extract_forecast(fitted.get_forecast(steps=len(test)))
    metrics = evaluate_forecast(test, test_pred)
    yield {"type": "progress",
           "step": f"RMSE={metrics['RMSE']}  MAPE={metrics['MAPE']}%", "pct": 82}

    end_year = int(grp.index.max()) + horizon
    yield {"type": "progress",
           "step": f"Refitting on full series → forecasting to {end_year}…", "pct": 93}
    final_model = fit_arima(grp, order)
    future_pred, future_lower, future_upper = _extract_forecast(final_model.get_forecast(steps=horizon))
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
                "lower": [float(v) for v in future_lower],
                "upper": [float(v) for v in future_upper],
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


def run_forecast_all_states(
    gini_annual_df: pd.DataFrame,
    gini_raw_df: pd.DataFrame = None,
) -> dict:
    """
    Fit ARIMA per state with BIC-based order selection.
    When gini_raw_df is provided, metrics are evaluated only on real survey years.
    """
    results = {}
    states = gini_annual_df["state"].unique()

    # Build per-state set of real survey years for honest evaluation
    survey_years_by_state = {}
    if gini_raw_df is not None:
        for state, grp in gini_raw_df.groupby("state"):
            survey_years_by_state[state] = set(grp["year"].tolist())

    for state in states:
        grp = gini_annual_df[gini_annual_df["state"] == state].set_index("year")["gini"]
        grp = grp.sort_index()

        if len(grp) < 10:
            continue

        n_real = len(survey_years_by_state.get(state, set()))
        p_max = 1 if n_real < SHORT_SERIES_THRESHOLD else 3

        train, test = train_test_split_ts(grp)
        stationarity = check_stationarity(train)
        order = select_order(train, p_max=p_max, q_max=p_max)
        print(f"    {state} (real obs={n_real}): selected ARIMA{order}")

        try:
            fitted = fit_arima(train, order)
            test_pred, _, _ = _extract_forecast(fitted.get_forecast(steps=len(test)))

            survey_yrs = survey_years_by_state.get(state, set())
            if survey_yrs:
                metrics = evaluate_on_survey_years(test, test_pred, survey_yrs)
                eval_mode = "survey_years_only"
            else:
                metrics = evaluate_forecast(test, test_pred)
                eval_mode = "all_test_years"

            final_model = fit_arima(grp, order)
            future_pred, future_lower, future_upper = _extract_forecast(
                final_model.get_forecast(steps=FORECAST_HORIZON)
            )
            future_years = list(range(grp.index.max() + 1, grp.index.max() + FORECAST_HORIZON + 1))

            results[state] = {
                "train_years":    list(map(int, train.index)),
                "train_gini":     [float(v) for v in train.values],
                "test_years":     list(map(int, test.index)),
                "test_gini":      [float(v) for v in test.values],
                "test_pred":      [float(v) for v in test_pred],
                "forecast_years": future_years,
                "forecast_gini":  [float(v) for v in future_pred],
                "forecast_lower": [float(v) for v in future_lower],
                "forecast_upper": [float(v) for v in future_upper],
                "metrics": {k: float(v) for k, v in metrics.items()},
                "eval_mode": eval_mode,
                "stationarity": {
                    "adf_stat":      float(stationarity["adf_stat"]),
                    "p_value":       float(stationarity["p_value"]),
                    "is_stationary": bool(stationarity["is_stationary"]),
                },
                "arima_order": list(order),
                "aic": round(float(final_model.aic), 2),
                "bic": round(float(final_model.bic), 2),
                "n_real_obs": n_real,
            }
        except Exception as e:
            results[state] = {"error": str(e)}

    with open(os.path.join(MODELS_DIR, "arima_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    return results


def plot_forecast(state: str, result: dict, save_path: str = None):
    if "error" in result:
        return None

    order_str = "ARIMA({},{},{})".format(*result["arima_order"])
    aic_str = f"AIC={result.get('aic', '?')}"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        f"Gini Coefficient Forecast — {state}  [{order_str}, {aic_str}]",
        fontsize=13, fontweight="bold",
    )

    ax = axes[0]
    ax.plot(result["train_years"], result["train_gini"], "b-o", markersize=4, label="Train")
    ax.plot(result["test_years"], result["test_gini"], "g-o", markersize=4, label="Test (actual)")
    ax.plot(result["test_years"], result["test_pred"], "r--o", markersize=4, label="Test (predicted)")
    ax.plot(result["forecast_years"], result["forecast_gini"], "m-^", markersize=5,
            label="Forecast 2023–2030")
    if "forecast_lower" in result:
        ax.fill_between(
            result["forecast_years"],
            result["forecast_lower"],
            result["forecast_upper"],
            color="violet", alpha=0.25, label="95% CI",
        )
    ax.axvline(x=result["test_years"][0], color="gray", linestyle=":", alpha=0.6)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("Historical + Forecast")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(result["test_years"], result["test_gini"], "g-o", label="Actual")
    ax2.plot(result["test_years"], result["test_pred"], "r--o", label="Predicted")
    m = result["metrics"]
    eval_note = " (survey yrs)" if result.get("eval_mode") == "survey_years_only" else ""
    ax2.set_title(
        f"Test Evaluation{eval_note}\nMAE={m['MAE']} | RMSE={m['RMSE']} | MAPE={m['MAPE']}%"
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
    valid = {s: r for s, r in results.items() if "error" not in r}
    states = list(valid.keys())
    mape = [r["metrics"]["MAPE"] for r in valid.values()]
    rmse = [r["metrics"]["RMSE"] for r in valid.values()]
    forecast_2030 = [r["forecast_gini"][-1] for r in valid.values()]
    orders = [str(tuple(r["arima_order"])) for r in valid.values()]

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle("Gini Forecasting Summary — All States (Auto-ARIMA, BIC selection)",
                 fontsize=13, fontweight="bold")

    colors_mape = ["#d73027" if v > 10 else "#fee090" if v > 5 else "#91cf60" for v in mape]
    axes[0].barh(states, mape, color=colors_mape)
    axes[0].set_xlabel("MAPE (%)")
    axes[0].set_title("Forecast Error (MAPE) by State")
    axes[0].axvline(x=np.mean(mape), color="red", linestyle="--",
                    label=f"Mean={np.mean(mape):.2f}%")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3, axis="x")

    axes[1].barh(states, rmse, color="steelblue")
    axes[1].set_xlabel("RMSE")
    axes[1].set_title("Forecast Error (RMSE) by State")
    axes[1].axvline(x=np.mean(rmse), color="red", linestyle="--",
                    label=f"Mean={np.mean(rmse):.4f}")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3, axis="x")

    colors_f = ["#d73027" if v > 0.4 else "#fee090" if v > 0.35 else "#91cf60" for v in forecast_2030]
    bars = axes[2].barh(states, forecast_2030, color=colors_f)
    axes[2].axvline(x=0.4, color="red", linestyle="--", label="Inequality threshold (0.40)")
    axes[2].set_xlabel("Gini Coefficient")
    axes[2].set_title("Forecasted Gini by 2030")
    for bar, order in zip(bars, orders):
        axes[2].text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                     order, va="center", fontsize=7, color="gray")
    axes[2].legend(fontsize=9)
    axes[2].grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def run_all(gini_annual_df: pd.DataFrame = None, gini_raw_df: pd.DataFrame = None) -> dict:
    if gini_annual_df is None:
        gini_annual_df = pd.read_csv(os.path.join(PROCESSED_DIR, "gini_state_annual.csv"))
    if gini_raw_df is None:
        raw_path = os.path.join(PROCESSED_DIR, "gini_state_clean.csv")
        if os.path.exists(raw_path):
            gini_raw_df = pd.read_csv(raw_path)

    print("Running auto-ARIMA forecasting per state (BIC order selection)...")
    results = run_forecast_all_states(gini_annual_df, gini_raw_df)

    success = sum(1 for r in results.values() if "error" not in r)
    print(f"  Forecast complete: {success}/{len(results)} states successful")

    for state, result in results.items():
        if "error" not in result:
            path = os.path.join(FIGURES_DIR, f"ts_{state.lower().replace(' ', '_')}.png")
            plot_forecast(state, result, save_path=path)

    plot_all_states_summary(
        results,
        save_path=os.path.join(FIGURES_DIR, "ts_summary_all_states.png"),
    )
    print("  Figures saved to outputs/figures/")
    return results


if __name__ == "__main__":
    run_all()
