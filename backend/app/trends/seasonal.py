import logging
from collections import defaultdict

from app.database import get_connection

logger = logging.getLogger(__name__)

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def get_seasonal_pattern(keyword: str) -> list[dict]:
    """
    Compute average search_volume by month-of-year across all available history.

    Returns [{month (1-12), label, avg, std, count}] for months with ≥2 data points.
    Returns [] if fewer than 2 distinct months have sufficient data.
    """
    try:
        import numpy as np
        _use_numpy = True
    except ImportError:
        _use_numpy = False

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT strftime('%m', recorded_at) as month, value
        FROM trend_data
        WHERE keyword = ?
          AND source = 'google_trends'
          AND metric = 'search_volume'
        ORDER BY recorded_at
        """,
        (keyword,),
    ).fetchall()
    conn.close()

    # Group values by month number
    monthly: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        month_num = int(row["month"])
        monthly[month_num].append(row["value"])

    result = []
    for month_num in range(1, 13):
        values = monthly.get(month_num, [])
        if len(values) < 2:
            continue
        if _use_numpy:
            import numpy as np
            avg = float(np.mean(values))
            std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        else:
            avg = sum(values) / len(values)
            variance = sum((v - avg) ** 2 for v in values) / (len(values) - 1) if len(values) > 1 else 0.0
            std = variance ** 0.5
        result.append({
            "month": month_num,
            "label": MONTH_LABELS[month_num - 1],
            "avg": round(avg, 2),
            "std": round(std, 2),
            "count": len(values),
        })

    if len(result) < 2:
        return []

    return result
