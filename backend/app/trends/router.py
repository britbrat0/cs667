import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, BackgroundTasks

from app.auth.service import get_current_user
from app.database import get_connection
from app.trends.service import get_top_trends, get_keyword_details, compute_composite_score
from app.scheduler.jobs import scrape_single_keyword

router = APIRouter(prefix="/api/trends", tags=["trends"])

# How old data can be before triggering on-demand scrape (in hours)
STALE_THRESHOLD_HOURS = 6


def _has_fresh_data(keyword: str) -> bool:
    """Check if we have recent data (< STALE_THRESHOLD_HOURS old) from all configured sources."""
    conn = get_connection()
    threshold = (datetime.now(timezone.utc) - timedelta(hours=STALE_THRESHOLD_HOURS)).isoformat()

    # Check that we have fresh data from each configured source, not just any source
    sources = conn.execute(
        "SELECT DISTINCT source FROM trend_data WHERE keyword = ? AND recorded_at >= ?",
        (keyword, threshold),
    ).fetchall()
    conn.close()

    fresh_sources = {r["source"] for r in sources}

    # At minimum we need google_trends; also require ebay/etsy if they are configured
    if "google_trends" not in fresh_sources:
        return False

    from app.config import settings
    if settings.ebay_app_id and settings.ebay_cert_id and "ebay" not in fresh_sources:
        return False
    if settings.etsy_api_key and "etsy" not in fresh_sources:
        return False

    return True


def _ensure_keyword_tracked(keyword: str):
    """Add keyword to keywords table if not already present."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO keywords (keyword, source, status) VALUES (?, 'user_search', 'active')",
        (keyword.lower().strip(),),
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
    keyword = keyword.lower().strip()
    _ensure_keyword_tracked(keyword)

    if not _has_fresh_data(keyword):
        # Run on-demand scrape in a background thread so we don't block
        # but also do a quick synchronous attempt for immediate results
        thread = threading.Thread(target=scrape_single_keyword, args=(keyword,))
        thread.start()
        thread.join(timeout=30)  # Wait up to 30 seconds for scrape

    # Return whatever data we have
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
    details = get_keyword_details(keyword.lower().strip(), period_days=period)
    return details


@router.get("/{keyword}/regions")
def trend_regions(keyword: str, scope: str = "us", user: str = Depends(get_current_user)):
    """Get region heatmap data for a keyword. scope: 'us' or 'global'."""
    keyword = keyword.lower().strip()
    conn = get_connection()

    if scope == "global":
        metric = "search_volume_region_global"
    else:
        metric = "search_volume_region"

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
    rows = conn.execute("SELECT keyword, source, status, added_at FROM keywords ORDER BY added_at DESC").fetchall()
    conn.close()
    return {"keywords": [dict(r) for r in rows]}


@router.post("/keywords/{keyword}/activate")
def activate_keyword(keyword: str, user: str = Depends(get_current_user)):
    """Promote a pending_review keyword to active."""
    conn = get_connection()
    conn.execute("UPDATE keywords SET status = 'active' WHERE keyword = ?", (keyword.lower().strip(),))
    conn.commit()
    conn.close()
    return {"message": f"Keyword '{keyword}' activated"}
