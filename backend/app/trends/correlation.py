import logging
from datetime import datetime, timedelta, timezone

from app.database import get_connection

logger = logging.getLogger(__name__)


def get_keyword_correlations(keyword: str, period_days: int = 30, top_n: int = 5) -> list[dict]:
    """
    Compute correlation of search_volume time-series between `keyword` and all other
    active keywords over the last `period_days` days.

    Returns up to top_n results sorted by abs(correlation) descending:
      [{keyword, correlation, direction}]
    Requires ≥5 overlapping data points; pairs with fewer are skipped.
    """
    try:
        import numpy as np
    except ImportError:
        logger.warning("numpy not available — correlation computation skipped")
        return []

    conn = get_connection()
    start = (datetime.now(timezone.utc) - timedelta(days=period_days)).isoformat()

    # Fetch search_volume for all active keywords
    rows = conn.execute(
        """
        SELECT t.keyword, DATE(t.recorded_at) as date, AVG(t.value) as value
        FROM trend_data t
        JOIN keywords k ON t.keyword = k.keyword
        WHERE t.metric = 'search_volume'
          AND t.source = 'google_trends'
          AND t.recorded_at >= ?
          AND k.status != 'inactive'
        GROUP BY t.keyword, DATE(t.recorded_at)
        ORDER BY t.keyword, date
        """,
        (start,),
    ).fetchall()
    conn.close()

    # Build dict: {kw: {date: value}}
    series: dict[str, dict[str, float]] = {}
    for row in rows:
        kw = row["keyword"]
        if kw not in series:
            series[kw] = {}
        series[kw][row["date"]] = row["value"]

    if keyword not in series:
        return []

    target_series = series[keyword]
    results = []

    for other_kw, other_data in series.items():
        if other_kw == keyword:
            continue

        # Find common dates
        common_dates = sorted(set(target_series.keys()) & set(other_data.keys()))
        if len(common_dates) < 5:
            continue

        x = np.array([target_series[d] for d in common_dates])
        y = np.array([other_data[d] for d in common_dates])

        # Skip if either series has zero variance
        if np.std(x) == 0 or np.std(y) == 0:
            continue

        corr_matrix = np.corrcoef(x, y)
        r = float(corr_matrix[0, 1])

        if np.isnan(r):
            continue

        direction = "positive" if r > 0 else "negative"
        results.append({"keyword": other_kw, "correlation": round(r, 3), "direction": direction})

    # Sort by absolute correlation descending, return top_n
    results.sort(key=lambda d: abs(d["correlation"]), reverse=True)
    return results[:top_n]
