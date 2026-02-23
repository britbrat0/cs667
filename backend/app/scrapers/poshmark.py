import time
import random
import re
import logging
from datetime import datetime, timezone

import requests
from app.database import get_connection

logger = logging.getLogger(__name__)

POSHMARK_SEARCH_URL = "https://poshmark.com/search"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def scrape_poshmark(keyword: str) -> bool:
    """Scrape Poshmark search results for a keyword. Returns True on success."""
    try:
        resp = requests.get(
            POSHMARK_SEARCH_URL,
            params={
                "query": keyword,
                "department": "All",
                "type": "listings",
            },
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=20,
        )

        if resp.status_code != 200:
            logger.warning(f"Poshmark returned {resp.status_code} for '{keyword}'")
            return False

        html = resp.text

        # Extract prices from embedded JSON state
        price_matches = re.findall(r'"price_amount"\s*:\s*\{[^}]*"val"\s*:\s*"(\d+\.?\d*)"', html)

        prices = []
        for p in price_matches:
            try:
                price = float(p)
                if 0 < price < 50000:
                    prices.append(price)
            except (ValueError, TypeError):
                continue

        # Also count total listings found
        original_price_matches = re.findall(r'"original_price"\s*:\s*"(\d+)"', html)
        listing_count = max(len(prices), len(original_price_matches))

        if not prices and listing_count == 0:
            logger.warning(f"No Poshmark listings found for '{keyword}'")
            return True

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()

        if prices:
            avg_price = sum(prices) / len(prices)
            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "poshmark", "avg_price", avg_price, now),
            )

            # Price volatility
            if len(prices) > 1:
                variance = sum((p - avg_price) ** 2 for p in prices) / (len(prices) - 1)
                volatility = variance ** 0.5
            else:
                volatility = 0.0

            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "poshmark", "price_volatility", volatility, now),
            )

        # Store listing count
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "poshmark", "listing_count", float(listing_count), now),
        )

        conn.commit()
        conn.close()

        avg_str = f"${avg_price:.2f}" if prices else "N/A"
        logger.info(f"Poshmark scrape complete for '{keyword}': {listing_count} listings, avg {avg_str}")
        time.sleep(random.uniform(1.0, 2.5))
        return True

    except Exception as e:
        logger.error(f"Poshmark scrape failed for '{keyword}': {e}")
        return False
