import logging
from datetime import datetime, timedelta, timezone

from app.database import get_connection

logger = logging.getLogger(__name__)

LIFECYCLE_STAGES = ["Emerging", "Accelerating", "Peak", "Saturation", "Decline", "Dormant"]


def _get_growth_rate(values_first_half: list[float], values_second_half: list[float]) -> float:
    """Calculate percentage growth between two halves of a time window."""
    if not values_first_half or not values_second_half:
        return 0.0
    avg_first = sum(values_first_half) / len(values_first_half)
    avg_second = sum(values_second_half) / len(values_second_half)
    if avg_first == 0:
        return 100.0 if avg_second > 0 else 0.0
    return ((avg_second - avg_first) / avg_first) * 100


def compute_composite_score(keyword: str, period_days: int) -> dict:
    """
    Compute composite trend score for a keyword over a time period.
    Returns dict with volume_growth, price_growth, composite_score, lifecycle_stage.
    """
    conn = get_connection()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=period_days)
    midpoint = now - timedelta(days=period_days / 2)

    # Volume metrics: search_volume (Google) + sold_count (eBay) + mention_count (Reddit) + listing_count (Depop)
    volume_metrics = ("search_volume", "sold_count", "mention_count", "listing_count")

    first_half_volumes = []
    second_half_volumes = []

    for metric in volume_metrics:
        rows = conn.execute(
            "SELECT value, recorded_at FROM trend_data WHERE keyword = ? AND metric = ? AND recorded_at >= ? ORDER BY recorded_at",
            (keyword, metric, start.isoformat()),
        ).fetchall()

        for row in rows:
            recorded = row["recorded_at"]
            if recorded < midpoint.isoformat():
                first_half_volumes.append(row["value"])
            else:
                second_half_volumes.append(row["value"])

    volume_growth = _get_growth_rate(first_half_volumes, second_half_volumes)

    # Price metrics: avg_price from eBay + Etsy
    price_rows = conn.execute(
        "SELECT value, recorded_at FROM trend_data WHERE keyword = ? AND source IN ('ebay', 'etsy', 'poshmark', 'depop') AND metric = 'avg_price' AND recorded_at >= ? ORDER BY recorded_at",
        (keyword, start.isoformat()),
    ).fetchall()

    first_half_prices = [r["value"] for r in price_rows if r["recorded_at"] < midpoint.isoformat()]
    second_half_prices = [r["value"] for r in price_rows if r["recorded_at"] >= midpoint.isoformat()]
    price_growth = _get_growth_rate(first_half_prices, second_half_prices)

    composite_score = 0.6 * volume_growth + 0.4 * price_growth

    scale_row = conn.execute(
        "SELECT scale FROM keywords WHERE keyword = ?", (keyword,)
    ).fetchone()
    scale = (scale_row["scale"] if scale_row and scale_row["scale"] else "macro")

    lifecycle_stage = _detect_lifecycle(keyword, volume_growth, composite_score, conn, start, scale)

    conn.close()

    return {
        "keyword": keyword,
        "period_days": period_days,
        "volume_growth": round(volume_growth, 2),
        "price_growth": round(price_growth, 2),
        "composite_score": round(composite_score, 2),
        "lifecycle_stage": lifecycle_stage,
        "scale": scale,
    }


def _detect_lifecycle(keyword: str, volume_growth: float, composite_score: float, conn, start, scale: str = "macro") -> str:
    """Determine lifecycle stage based on volume levels and growth trajectory.
    Scale-aware: micro trends use lower absolute volume thresholds."""
    volume_rows = conn.execute(
        "SELECT SUM(value) as total FROM trend_data WHERE keyword = ? AND metric IN ('search_volume', 'sold_count', 'mention_count', 'listing_count') AND recorded_at >= ?",
        (keyword, start.isoformat()),
    ).fetchone()

    total_volume = volume_rows["total"] if volume_rows["total"] else 0

    prev_scores = conn.execute(
        "SELECT composite_score FROM trend_scores WHERE keyword = ? ORDER BY computed_at DESC LIMIT 3",
        (keyword,),
    ).fetchall()
    prev_score_values = [r["composite_score"] for r in prev_scores if r["composite_score"] is not None]
    acceleration = (composite_score - prev_score_values[0]) if len(prev_score_values) >= 2 else 0

    # Micro trends operate at much lower absolute volumes
    is_micro = scale == "micro"
    dormant_thresh = 2 if is_micro else 5
    emerging_vol_thresh = 15 if is_micro else 100
    peak_vol_thresh = 5 if is_micro else 50

    if total_volume < dormant_thresh:
        return "Dormant"
    elif volume_growth > 30 and total_volume < emerging_vol_thresh:
        return "Emerging"
    elif volume_growth > 20 and acceleration > 0:
        return "Accelerating"
    elif -5 <= volume_growth <= 10 and total_volume > peak_vol_thresh:
        if acceleration <= 0:
            return "Peak"
        return "Accelerating"
    elif -20 <= volume_growth < -5:
        return "Saturation"
    elif volume_growth < -20:
        return "Decline"
    else:
        if volume_growth > 10:
            return "Emerging"
        return "Peak"


def predict_stage_warning(current_stage: str, current_vg: float, projected_vg: float, slope: float) -> str | None:
    """Return a human-readable warning if the trend is likely to transition lifecycle stages
    within the next 7 days, or None if the stage looks stable."""
    if current_stage == "Emerging" and projected_vg > 30 and slope > 1.5:
        return "Approaching Accelerating"
    if current_stage == "Accelerating" and slope > 2.0 and projected_vg > 45:
        return "Nearing Peak"
    if current_stage == "Accelerating" and slope < -1.5:
        return "Growth slowing"
    if current_stage == "Peak" and slope < -1.5:
        return "Entering Saturation"
    if current_stage == "Saturation" and slope < -2.5:
        return "Approaching Decline"
    if current_stage == "Decline" and slope < -3.5:
        return "Nearing Dormant"
    if current_stage == "Dormant" and slope > 1.5:
        return "Signs of Revival"
    return None


def compute_and_store_scores(keyword: str):
    """Compute scores for all standard time periods and store in trend_scores."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    for period in [7, 14, 30, 60, 90]:
        result = compute_composite_score(keyword, period)

        # Delete old score for this keyword + period
        conn.execute(
            "DELETE FROM trend_scores WHERE keyword = ? AND period_days = ?",
            (keyword, period),
        )

        conn.execute(
            "INSERT INTO trend_scores (keyword, period_days, volume_growth, price_growth, composite_score, lifecycle_stage, computed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (keyword, period, result["volume_growth"], result["price_growth"], result["composite_score"], result["lifecycle_stage"], now),
        )

    conn.commit()
    conn.close()


def get_top_trends(period_days: int = 7, limit: int = 10) -> list[dict]:
    """Get top N trends ranked by composite score for a given period.
    Uses within-group percentile ranking so micro trends can surface alongside macro trends."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ts.keyword, ts.composite_score, ts.volume_growth, ts.price_growth, ts.lifecycle_stage, ts.computed_at, k.source, COALESCE(k.scale, 'macro') as scale "
        "FROM trend_scores ts LEFT JOIN keywords k ON ts.keyword = k.keyword "
        "WHERE ts.period_days = ? AND (k.status IS NULL OR k.status != 'inactive') "
        "ORDER BY ts.composite_score DESC",
        (period_days,),
    ).fetchall()
    conn.close()

    all_trends = [dict(r) for r in rows]

    macro = sorted([t for t in all_trends if t["scale"] == "macro"], key=lambda t: t["composite_score"] or 0, reverse=True)
    micro = sorted([t for t in all_trends if t["scale"] == "micro"], key=lambda t: t["composite_score"] or 0, reverse=True)

    def assign_percentile(group):
        n = len(group)
        for i, t in enumerate(group):
            t["_pct"] = (n - i) / n if n > 0 else 0.5
        return group

    combined = sorted(
        assign_percentile(macro) + assign_percentile(micro),
        key=lambda t: t["_pct"],
        reverse=True,
    )

    return [
        {
            "rank": i + 1,
            "keyword": t["keyword"],
            "composite_score": t["composite_score"],
            "volume_growth": t["volume_growth"],
            "price_growth": t["price_growth"],
            "lifecycle_stage": t["lifecycle_stage"],
            "computed_at": t["computed_at"],
            "source": t["source"] or "seed",
            "scale": t["scale"],
        }
        for i, t in enumerate(combined[:limit])
    ]


def get_keyword_details(keyword: str, period_days: int = 7) -> dict:
    """Get full trend detail for a keyword: time series, price, volume, volatility, regions."""
    conn = get_connection()
    start = (datetime.now(timezone.utc) - timedelta(days=period_days)).isoformat()

    # Score
    score_row = conn.execute(
        "SELECT * FROM trend_scores WHERE keyword = ? AND period_days = ? ORDER BY computed_at DESC LIMIT 1",
        (keyword, period_days),
    ).fetchone()

    # Search volume over time
    search_volume = conn.execute(
        "SELECT value, recorded_at FROM trend_data WHERE keyword = ? AND source = 'google_trends' AND metric = 'search_volume' AND recorded_at >= ? ORDER BY recorded_at",
        (keyword, start),
    ).fetchall()

    # Avg price over time — one point per day, averaged across all marketplace sources
    ebay_prices = conn.execute(
        "SELECT AVG(value) as value, DATE(recorded_at) as recorded_at FROM trend_data "
        "WHERE keyword = ? AND source IN ('ebay', 'etsy', 'poshmark', 'depop') AND metric = 'avg_price' AND recorded_at >= ? "
        "GROUP BY DATE(recorded_at) ORDER BY recorded_at",
        (keyword, start),
    ).fetchall()

    # Sales/listing volume over time — one point per day, summed across sources
    sales_volume = conn.execute(
        "SELECT SUM(value) as value, DATE(recorded_at) as recorded_at FROM trend_data "
        "WHERE keyword = ? AND source IN ('ebay', 'etsy', 'poshmark', 'depop') AND metric IN ('sold_count', 'listing_count') AND recorded_at >= ? "
        "GROUP BY DATE(recorded_at) ORDER BY recorded_at",
        (keyword, start),
    ).fetchall()

    # Price volatility (latest from any source)
    volatility = conn.execute(
        "SELECT value, recorded_at FROM trend_data WHERE keyword = ? AND source IN ('ebay', 'etsy', 'poshmark', 'depop') AND metric = 'price_volatility' AND recorded_at >= ? ORDER BY recorded_at DESC LIMIT 1",
        (keyword, start),
    ).fetchone()

    # Region data — US
    us_regions = conn.execute(
        "SELECT region, value FROM trend_data WHERE keyword = ? AND metric = 'search_volume_region' AND recorded_at >= ? ORDER BY value DESC",
        (keyword, start),
    ).fetchall()

    # Region data — global
    global_regions = conn.execute(
        "SELECT region, value FROM trend_data WHERE keyword = ? AND metric = 'search_volume_region_global' AND recorded_at >= ? ORDER BY value DESC",
        (keyword, start),
    ).fetchall()

    conn.close()

    return {
        "keyword": keyword,
        "period_days": period_days,
        "score": dict(score_row) if score_row else None,
        "search_volume": [{"value": r["value"], "date": r["recorded_at"]} for r in search_volume],
        "ebay_avg_price": [{"value": r["value"], "date": r["recorded_at"]} for r in ebay_prices],
        "sales_volume": [{"value": r["value"], "date": r["recorded_at"]} for r in sales_volume],
        "price_volatility": volatility["value"] if volatility else None,
        "regions_us": [{"region": r["region"], "value": r["value"]} for r in us_regions],
        "regions_global": [{"region": r["region"], "value": r["value"]} for r in global_regions],
    }
