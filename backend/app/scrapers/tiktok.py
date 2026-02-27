import asyncio
import logging
from datetime import datetime, timezone

from app.database import get_connection

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _sia = SentimentIntensityAnalyzer()
except ImportError:
    _sia = None

logger = logging.getLogger(__name__)


async def _scrape_tiktok_async(keyword: str) -> list[dict]:
    """Fetch up to 30 TikTok videos for a keyword and return desc + playCount."""
    try:
        from TikTokApi import TikTokApi
        results = []
        async with TikTokApi() as api:
            await api.create_sessions(num_sessions=1, sleep_after=3, headless=True)
            async for video in api.search.videos(keyword, count=30):
                desc = video.as_dict.get("desc", "")
                play_count = video.as_dict.get("stats", {}).get("playCount", 0)
                results.append({"desc": desc, "play_count": play_count})
        return results
    except Exception as e:
        logger.warning(f"TikTok async fetch failed for '{keyword}': {e}")
        return []


def scrape_tiktok(keyword: str) -> bool:
    """Scrape TikTok for keyword videos. Non-fatal — failures are logged as warnings."""
    try:
        videos = asyncio.run(_scrape_tiktok_async(keyword))

        if not videos:
            logger.warning(f"No TikTok data for '{keyword}'")
            return False

        mention_count = float(len(videos))
        total_views = float(sum(v["play_count"] for v in videos))
        avg_views = total_views / mention_count if mention_count > 0 else 0.0

        descs = [v["desc"] for v in videos if v.get("desc")]
        avg_sentiment = 0.0
        if _sia and descs:
            avg_sentiment = sum(_sia.polarity_scores(d)["compound"] for d in descs) / len(descs)

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "tiktok", "tiktok_mentions", mention_count, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "tiktok", "tiktok_views", avg_views, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "tiktok", "tiktok_sentiment", avg_sentiment, now),
        )
        conn.commit()
        conn.close()

        logger.info(f"TikTok scrape complete for '{keyword}': {int(mention_count)} videos, {int(total_views)} total views")
        return True

    except Exception as e:
        logger.warning(f"TikTok scrape failed for '{keyword}': {e}")
        return False
