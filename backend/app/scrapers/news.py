import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from app.database import get_connection

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _sia = SentimentIntensityAnalyzer()
except ImportError:
    _sia = None

logger = logging.getLogger(__name__)

USER_AGENT = "FashionTrendForecaster/0.1 (educational project)"
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text).strip()


def scrape_news(keyword: str) -> bool:
    """Scrape Google News RSS for articles mentioning this keyword in a fashion context.

    Stores two metrics in trend_data:
      - news_mentions  : number of articles returned (proxy for media buzz)
      - news_sentiment : average VADER compound score of title + description text
    """
    try:
        query = urllib.parse.quote(f"{keyword} fashion")
        url = (
            f"https://news.google.com/rss/search"
            f"?q={query}&hl=en-US&gl=US&ceid=US:en"
        )

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        texts = []
        for item in items:
            title = _strip_html(item.findtext("title") or "")
            description = _strip_html(item.findtext("description") or "")
            combined = f"{title} {description}".strip()
            if combined:
                texts.append(combined)

        count = len(texts)
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "news", "news_mentions", float(count), now),
        )

        if _sia and texts:
            avg_sentiment = sum(_sia.polarity_scores(t)["compound"] for t in texts) / len(texts)
            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "news", "news_sentiment", avg_sentiment, now),
            )

        conn.commit()
        conn.close()

        logger.info(f"News scrape complete for '{keyword}': {count} articles")
        return True

    except Exception as e:
        logger.warning(f"News scrape failed for '{keyword}': {e}")
        return False
