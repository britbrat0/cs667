import logging
from datetime import datetime, timedelta

import numpy as np

from app.database import get_connection

logger = logging.getLogger(__name__)

MIN_POINTS = 7        # Minimum data points required to produce a forecast
FIT_WINDOW = 21       # Use the most recent N days for fitting
POLY_DEGREE = 1       # Linear regression: stable and interpretable for short-term forecasts
CONFIDENCE_Z = 1.96   # 95% confidence interval


def forecast_search_volume(keyword: str, horizon_days: int = 14) -> dict:
    """
    Forecast future Google Trends search volume using polynomial regression.

    Fits a degree-2 polynomial to the most recent FIT_WINDOW days of daily
    search volume, then projects horizon_days forward with a 95% confidence
    interval derived from the fit residuals.

    Returns a dict with:
      - historical: list of {date, value}
      - forecast:   list of {date, value, lower, upper}
      - insufficient_data: True if not enough history exists
      - fit_window_days: number of days used for fitting
      - model: description string
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT AVG(value) as value, DATE(recorded_at) as date "
        "FROM trend_data "
        "WHERE keyword = ? AND source = 'google_trends' AND metric = 'search_volume' "
        "GROUP BY DATE(recorded_at) ORDER BY date ASC",
        (keyword,),
    ).fetchall()
    conn.close()

    historical = [{"date": r["date"], "value": float(r["value"])} for r in rows]

    if len(historical) < MIN_POINTS:
        return {
            "keyword": keyword,
            "historical": historical,
            "forecast": [],
            "insufficient_data": True,
            "fit_window_days": 0,
            "model": "none",
        }

    # Fit on the most recent FIT_WINDOW days (or all data if less)
    fit_data = historical[-FIT_WINDOW:]
    y = np.array([d["value"] for d in fit_data])
    x = np.arange(len(y), dtype=float)

    degree = min(POLY_DEGREE, len(y) - 1)
    coeffs = np.polyfit(x, y, deg=degree)

    # Residuals → standard deviation for confidence interval
    y_fitted = np.polyval(coeffs, x)
    residuals = y - y_fitted
    std = float(np.std(residuals)) if len(residuals) > 1 else 5.0

    # Project forward
    last_date = datetime.strptime(historical[-1]["date"], "%Y-%m-%d")
    x_offset = len(y)  # x position right after the last training point
    forecast = []
    for i in range(horizon_days):
        xi = float(x_offset + i)
        val = float(np.polyval(coeffs, xi))
        val = float(np.clip(val, 0, 100))
        lower = float(np.clip(val - CONFIDENCE_Z * std, 0, 100))
        upper = float(np.clip(val + CONFIDENCE_Z * std, 0, 100))
        future_date = (last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        forecast.append({"date": future_date, "value": val, "lower": lower, "upper": upper})

    logger.info(
        f"Forecast generated for '{keyword}': horizon={horizon_days}d, "
        f"fit_window={len(fit_data)}d, std={std:.2f}"
    )

    return {
        "keyword": keyword,
        "historical": historical,
        "forecast": forecast,
        "insufficient_data": False,
        "fit_window_days": len(fit_data),
        "model": f"polynomial_deg{degree}",
    }
