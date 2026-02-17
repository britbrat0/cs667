import logging
from datetime import datetime, timezone

from app.config import settings
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


def _get_reddit_client():
    """Create a PRAW Reddit client. Returns None if credentials are not configured."""
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        logger.warning("Reddit API credentials not configured — skipping Reddit scraping")
        return None

    try:
        import praw
        return praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent="FashionTrendForecaster/0.1",
        )
    except Exception as e:
        logger.error(f"Failed to create Reddit client: {e}")
        return None


def scrape_reddit(keyword: str) -> bool:
    """Scrape Reddit for mentions of a keyword across fashion subreddits. Returns True on success."""
    reddit = _get_reddit_client()
    if reddit is None:
        return True  # Not an error, just not configured

    try:
        total_mentions = 0

        for sub_name in FASHION_SUBREDDITS:
            try:
                subreddit = reddit.subreddit(sub_name)
                results = subreddit.search(keyword, sort="new", time_filter="week", limit=100)
                count = sum(1 for _ in results)
                total_mentions += count
            except Exception as e:
                logger.warning(f"Failed to search r/{sub_name} for '{keyword}': {e}")
                continue

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
    """Discover new fashion keywords from trending Reddit posts. Returns list of candidate keywords."""
    reddit = _get_reddit_client()
    if reddit is None:
        return []

    candidates = []
    try:
        for sub_name in FASHION_SUBREDDITS:
            try:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.hot(limit=25):
                    title = post.title.lower()
                    # Simple extraction: collect multi-word phrases from titles
                    # More sophisticated NLP could be added later
                    candidates.append(title)
            except Exception as e:
                logger.warning(f"Failed to get trending from r/{sub_name}: {e}")
                continue
    except Exception as e:
        logger.error(f"Reddit discovery failed: {e}")

    return candidates
