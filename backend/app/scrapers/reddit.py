import time
import random
import logging
from datetime import datetime, timezone

import requests
from app.database import get_connection

logger = logging.getLogger(__name__)

FASHION_SUBREDDITS = [
    "fashion",
    "streetwear",
    "malefashionadvice",
    "femalefashionadvice",
    "thriftstorehauls",
    "Depop",
    "VintageFashion",
]

USER_AGENT = "FashionTrendForecaster/0.1 (educational project)"


def _reddit_json_get(url: str) -> dict | None:
    """Fetch a Reddit JSON endpoint with rate-limit-friendly headers."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code == 429:
            logger.warning("Reddit rate limited, backing off")
            time.sleep(5)
            return None
        if resp.status_code != 200:
            logger.warning(f"Reddit returned {resp.status_code} for {url}")
            return None
        return resp.json()
    except Exception as e:
        logger.warning(f"Reddit request failed for {url}: {e}")
        return None


def scrape_reddit(keyword: str) -> bool:
    """Scrape Reddit for mentions of a keyword across fashion subreddits using public JSON endpoints."""
    try:
        total_mentions = 0

        for sub_name in FASHION_SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub_name}/search.json?q={requests.utils.quote(keyword)}&restrict_sr=1&sort=new&t=week&limit=100"
            data = _reddit_json_get(url)

            if data and "data" in data:
                children = data["data"].get("children", [])
                total_mentions += len(children)

            # Be respectful with rate limiting
            time.sleep(random.uniform(1.0, 2.0))

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "reddit", "mention_count", float(total_mentions), now),
        )
        conn.commit()
        conn.close()

        logger.info(f"Reddit scrape complete for '{keyword}': {total_mentions} mentions")
        return True

    except Exception as e:
        logger.error(f"Reddit scrape failed for '{keyword}': {e}")
        return False


def discover_trending_keywords() -> list[str]:
    """Discover new fashion keywords from trending Reddit posts using public JSON endpoints."""
    candidates = []
    try:
        for sub_name in FASHION_SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub_name}/hot.json?limit=25"
            data = _reddit_json_get(url)

            if data and "data" in data:
                for child in data["data"].get("children", []):
                    title = child.get("data", {}).get("title", "").lower()
                    if title:
                        candidates.append(title)

            time.sleep(random.uniform(1.0, 2.0))

    except Exception as e:
        logger.error(f"Reddit discovery failed: {e}")

    return candidates
