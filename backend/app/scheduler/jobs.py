import logging
import time
import random
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.scrapers.google_trends import scrape_google_trends
from app.scrapers.ebay import scrape_ebay
from app.scrapers.reddit import scrape_reddit
from app.scrapers.depop import scrape_depop
from app.scrapers.etsy import scrape_etsy
from app.scrapers.poshmark import scrape_poshmark
from app.scrapers.discovery import get_active_keywords, run_discovery
from app.database import get_connection
from app.trends.service import compute_and_store_scores

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scrape_all_sources():
    """Scrape all data sources for all active keywords."""
    keywords = get_active_keywords()
    logger.info(f"Starting scheduled scrape for {len(keywords)} keywords")

    for keyword in keywords:
        logger.info(f"Scraping keyword: '{keyword}'")
        scrape_google_trends(keyword)
        scrape_ebay(keyword)
        scrape_reddit(keyword)
        scrape_depop(keyword)
        scrape_etsy(keyword)
        scrape_poshmark(keyword)
        time.sleep(random.uniform(5, 10))  # pause between keywords to avoid rate limits

    logger.info("Scheduled scrape complete")


def compute_all_scores():
    """Recompute composite scores for all active keywords."""
    keywords = get_active_keywords()
    logger.info(f"Computing scores for {len(keywords)} keywords")

    for keyword in keywords:
        try:
            compute_and_store_scores(keyword)
        except Exception as e:
            logger.error(f"Failed to compute scores for '{keyword}': {e}")

    logger.info("Score computation complete")


def scrape_and_score():
    """Combined job: scrape all sources, then compute scores."""
    scrape_all_sources()
    compute_all_scores()


def discover_keywords():
    """Run keyword auto-discovery."""
    run_discovery()


def expire_stale_keywords():
    """Deactivate user_search keywords not searched in the last 30 days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    conn = get_connection()
    result = conn.execute(
        "UPDATE keywords SET status = 'inactive' WHERE source = 'user_search' AND status = 'active' AND (last_searched_at IS NULL OR last_searched_at < ?)",
        (cutoff,),
    )
    expired = result.rowcount
    conn.commit()
    conn.close()
    if expired:
        logger.info(f"Auto-expired {expired} stale user-searched keyword(s)")


def scrape_single_keyword(keyword: str):
    """On-demand scrape for a single keyword across all sources."""
    logger.info(f"On-demand scrape for '{keyword}'")
    scrape_google_trends(keyword)
    scrape_ebay(keyword)
    scrape_reddit(keyword)
    scrape_depop(keyword)
    scrape_etsy(keyword)
    scrape_poshmark(keyword)
    compute_and_store_scores(keyword)
    logger.info(f"On-demand scrape and scoring complete for '{keyword}'")


def start_scheduler():
    """Initialize and start the background scheduler."""
    # Scrape + score every 6 hours
    scheduler.add_job(scrape_and_score, "interval", hours=6, id="scrape_and_score", replace_existing=True)

    # Auto-discover new keywords every 24 hours
    scheduler.add_job(discover_keywords, "interval", hours=24, id="discover_keywords", replace_existing=True)

    # Expire stale user-searched keywords daily
    scheduler.add_job(expire_stale_keywords, "interval", hours=24, id="expire_stale_keywords", replace_existing=True)

    scheduler.start()
    logger.info("Scheduler started: scrape_and_score every 6h, discover_keywords every 24h, expire_stale_keywords every 24h")


def stop_scheduler():
    """Shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
