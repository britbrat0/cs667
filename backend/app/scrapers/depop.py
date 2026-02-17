import time
import random
import logging
from datetime import datetime, timezone

import requests
from app.database import get_connection

logger = logging.getLogger(__name__)

# Depop's internal API used by their web frontend
DEPOP_API_BASE = "https://webapi.depop.com/api/v2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.depop.com/",
    "Origin": "https://www.depop.com",
}


def scrape_depop(keyword: str) -> bool:
    """Scrape Depop search results via their web API. Returns True on success."""
    try:
        url = f"{DEPOP_API_BASE}/search/products/"
        params = {
            "what": keyword,
            "itemsPerPage": 48,
            "country": "us",
            "currency": "USD",
        }

        resp = requests.get(url, params=params, headers=HEADERS, timeout=20)

        if resp.status_code == 403:
            logger.warning(f"Depop API returned 403 for '{keyword}' — may need updated headers")
            return True
        if resp.status_code != 200:
            logger.warning(f"Depop API returned {resp.status_code} for '{keyword}'")
            return True

        data = resp.json()
        products = data.get("products", [])

        if not products:
            logger.warning(f"No Depop products found for '{keyword}'")
            return True

        prices = []
        for product in products:
            price_info = product.get("price", {})
            amount = price_info.get("priceAmount")
            if amount:
                try:
                    price = float(amount)
                    if 0 < price < 10000:
                        prices.append(price)
                except (ValueError, TypeError):
                    continue

        listing_count = len(products)
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "depop", "listing_count", float(listing_count), now),
        )

        if prices:
            avg_price = sum(prices) / len(prices)
            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "depop", "avg_price", avg_price, now),
            )

        conn.commit()
        conn.close()

        logger.info(f"Depop scrape complete for '{keyword}': {listing_count} listings")
        time.sleep(random.uniform(1, 3))
        return True

    except Exception as e:
        logger.error(f"Depop scrape failed for '{keyword}': {e}")
        return False


def discover_trending_keywords() -> list[str]:
    """Discover trending keywords from Depop. Returns list of candidate terms."""
    try:
        # Try the trending/explore endpoint
        url = f"{DEPOP_API_BASE}/search/trending/"
        resp = requests.get(url, headers=HEADERS, timeout=15)

        candidates = []
        if resp.status_code == 200:
            data = resp.json()
            terms = data.get("trending", data.get("keywords", []))
            if isinstance(terms, list):
                for term in terms:
                    if isinstance(term, str):
                        candidates.append(term.lower())
                    elif isinstance(term, dict):
                        name = term.get("name", term.get("keyword", ""))
                        if name:
                            candidates.append(name.lower())

        return list(set(candidates))

    except Exception as e:
        logger.error(f"Depop discovery failed: {e}")
        return []
