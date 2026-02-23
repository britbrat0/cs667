import time
import random
import logging
from datetime import datetime, timezone

from pytrends.request import TrendReq
from app.database import get_connection

logger = logging.getLogger(__name__)


def scrape_google_trends(keyword: str, retries: int = 3) -> bool:
    """Scrape Google Trends for a keyword. Retries up to `retries` times on 429. Returns True on success."""
    for attempt in range(retries):
        result = _scrape_google_trends_once(keyword)
        if result:
            return True
        wait = 60 * (2 ** attempt)  # 60s, 120s, 240s
        logger.warning(f"Google Trends rate limited for '{keyword}', retrying in {wait}s (attempt {attempt + 1}/{retries})")
        time.sleep(wait)
    logger.error(f"Google Trends scrape failed for '{keyword}' after {retries} attempts")
    return False


def _scrape_google_trends_once(keyword: str) -> bool:
    """Single attempt to scrape Google Trends for a keyword."""
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload([keyword], timeframe="today 3-m", geo="US")

        # Interest over time
        interest_df = pytrends.interest_over_time()
        if not interest_df.empty and keyword in interest_df.columns:
            conn = get_connection()
            for date, row in interest_df.iterrows():
                conn.execute(
                    "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                    (keyword, "google_trends", "search_volume", float(row[keyword]), date.isoformat()),
                )
            conn.commit()
            conn.close()

        time.sleep(random.uniform(1, 3))

        # Interest by region — US states
        try:
            pytrends.build_payload([keyword], timeframe="today 3-m", geo="US")
            region_df = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True)
            if not region_df.empty and keyword in region_df.columns:
                conn = get_connection()
                now = datetime.now(timezone.utc).isoformat()
                for region, row in region_df.iterrows():
                    if row[keyword] > 0:
                        conn.execute(
                            "INSERT INTO trend_data (keyword, source, metric, value, region, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (keyword, "google_trends", "search_volume_region", float(row[keyword]), region, now),
                        )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to get US region data for '{keyword}': {e}")

        time.sleep(random.uniform(1, 3))

        # Interest by region — worldwide
        try:
            pytrends.build_payload([keyword], timeframe="today 3-m")
            world_df = pytrends.interest_by_region(resolution="COUNTRY", inc_low_vol=True)
            if not world_df.empty and keyword in world_df.columns:
                conn = get_connection()
                now = datetime.now(timezone.utc).isoformat()
                for country, row in world_df.iterrows():
                    if row[keyword] > 0:
                        conn.execute(
                            "INSERT INTO trend_data (keyword, source, metric, value, region, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (keyword, "google_trends", "search_volume_region_global", float(row[keyword]), country, now),
                        )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to get global region data for '{keyword}': {e}")

        logger.info(f"Google Trends scrape complete for '{keyword}'")
        return True

    except Exception as e:
        logger.error(f"Google Trends scrape failed for '{keyword}': {e}")
        return False
