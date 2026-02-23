import threading
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException

from app.auth.service import get_current_user
from app.database import get_connection
from app.trends.service import get_top_trends, get_keyword_details, compute_composite_score
from app.scheduler.jobs import scrape_single_keyword

router = APIRouter(prefix="/api/trends", tags=["trends"])

# How old data can be before triggering on-demand scrape (in hours)
STALE_THRESHOLD_HOURS = 6

# Auto-expire user_search keywords inactive for this many days
USER_KEYWORD_EXPIRY_DAYS = 30


def _normalize(keyword: str) -> str:
    """Normalize keyword: lowercase, strip, collapse whitespace."""
    return re.sub(r'\s+', ' ', keyword.lower().strip())


def _is_duplicate(keyword: str, conn) -> bool:
    """Check if a normalized keyword already exists under a different form."""
    row = conn.execute(
        "SELECT keyword FROM keywords WHERE keyword = ? AND status != 'inactive'",
        (keyword,),
    ).fetchone()
    return row is not None


def _has_fresh_data(keyword: str) -> bool:
    """Check if we have recent data (< STALE_THRESHOLD_HOURS old) from all configured sources."""
    conn = get_connection()
    threshold = (datetime.now(timezone.utc) - timedelta(hours=STALE_THRESHOLD_HOURS)).isoformat()

    sources = conn.execute(
        "SELECT DISTINCT source FROM trend_data WHERE keyword = ? AND recorded_at >= ?",
        (keyword, threshold),
    ).fetchall()
    conn.close()

    fresh_sources = {r["source"] for r in sources}

    if "google_trends" not in fresh_sources:
        return False

    from app.config import settings
    if settings.ebay_app_id and settings.ebay_cert_id and "ebay" not in fresh_sources:
        return False
    if settings.etsy_api_key and "etsy" not in fresh_sources:
        return False

    return True


def _ensure_keyword_tracked(keyword: str):
    """Add keyword to keywords table if not already present. Updates last_searched_at on each search."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    existing = conn.execute(
        "SELECT keyword, status FROM keywords WHERE keyword = ?", (keyword,)
    ).fetchone()

    if existing:
        # Reactivate if previously deactivated, and update last searched time
        conn.execute(
            "UPDATE keywords SET last_searched_at = ?, status = CASE WHEN status = 'inactive' THEN 'active' ELSE status END WHERE keyword = ?",
            (now, keyword),
        )
    else:
        conn.execute(
            "INSERT INTO keywords (keyword, source, status, last_searched_at) VALUES (?, 'user_search', 'active', ?)",
            (keyword, now),
        )

    conn.commit()
    conn.close()


@router.get("/top")
def top_trends(period: int = 7, user: str = Depends(get_current_user)):
    """Get top 10 emerging trends for a given time period."""
    trends = get_top_trends(period_days=period, limit=10)
    return {
        "period_days": period,
        "trends": trends,
    }


@router.get("/search")
def search_trend(keyword: str, period: int = 7, background_tasks: BackgroundTasks = None, user: str = Depends(get_current_user)):
    """Search a custom keyword. Triggers on-demand scrape if no fresh data."""
    keyword = _normalize(keyword)
    _ensure_keyword_tracked(keyword)

    if not _has_fresh_data(keyword):
        thread = threading.Thread(target=scrape_single_keyword, args=(keyword,))
        thread.start()
        thread.join(timeout=30)

    details = get_keyword_details(keyword, period_days=period)
    score = compute_composite_score(keyword, period)

    return {
        "keyword": keyword,
        "period_days": period,
        "score": score,
        "details": details,
    }


@router.get("/{keyword}/details")
def trend_details(keyword: str, period: int = 7, user: str = Depends(get_current_user)):
    """Get full trend detail for a specific keyword."""
    details = get_keyword_details(_normalize(keyword), period_days=period)
    return details


@router.get("/{keyword}/forecast")
def trend_forecast(keyword: str, horizon: int = 14, user: str = Depends(get_current_user)):
    """Forecast future search volume for a keyword using polynomial regression."""
    from app.forecasting.model import forecast_search_volume
    return forecast_search_volume(_normalize(keyword), horizon_days=horizon)


@router.get("/{keyword}/regions")
def trend_regions(keyword: str, scope: str = "us", user: str = Depends(get_current_user)):
    """Get region heatmap data for a keyword. scope: 'us' or 'global'."""
    keyword = _normalize(keyword)
    conn = get_connection()

    metric = "search_volume_region_global" if scope == "global" else "search_volume_region"

    rows = conn.execute(
        "SELECT region, value FROM trend_data WHERE keyword = ? AND metric = ? ORDER BY value DESC",
        (keyword, metric),
    ).fetchall()
    conn.close()

    return {
        "keyword": keyword,
        "scope": scope,
        "regions": [{"region": r["region"], "value": r["value"]} for r in rows],
    }


@router.get("/keywords/list")
def list_keywords(user: str = Depends(get_current_user)):
    """List all tracked keywords and their status."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT keyword, source, status, added_at, last_searched_at FROM keywords WHERE status != 'inactive' ORDER BY added_at DESC"
    ).fetchall()
    conn.close()
    return {"keywords": [dict(r) for r in rows]}


@router.post("/keywords/{keyword}/activate")
def activate_keyword(keyword: str, user: str = Depends(get_current_user)):
    """Promote a pending_review keyword to active."""
    conn = get_connection()
    conn.execute("UPDATE keywords SET status = 'active' WHERE keyword = ?", (_normalize(keyword),))
    conn.commit()
    conn.close()
    return {"message": f"Keyword '{keyword}' activated"}


@router.delete("/keywords/{keyword}")
def remove_keyword(keyword: str, user: str = Depends(get_current_user)):
    """Deactivate a user-searched keyword. Seed keywords are protected."""
    keyword = _normalize(keyword)
    conn = get_connection()

    row = conn.execute(
        "SELECT source FROM keywords WHERE keyword = ?", (keyword,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Keyword '{keyword}' not found")

    if row["source"] == "seed":
        conn.close()
        raise HTTPException(status_code=403, detail="Seed keywords cannot be removed")

    conn.execute("UPDATE keywords SET status = 'inactive' WHERE keyword = ?", (keyword,))
    conn.commit()
    conn.close()
    return {"message": f"Keyword '{keyword}' removed"}
