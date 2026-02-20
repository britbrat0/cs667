import time
import random
import logging
from datetime import datetime, timezone

import requests
from app.config import settings
from app.database import get_connection

logger = logging.getLogger(__name__)

ETSY_BASE_URL = "https://openapi.etsy.com/v3/application/listings/active"

# Etsy taxonomy ID for Clothing (category)
CLOTHING_TAXONOMY_ID = 1


def scrape_etsy(keyword: str) -> bool:
    """Scrape Etsy active listings for a keyword. Returns True on success."""
    if not settings.etsy_api_key:
        logger.warning("Etsy API key not configured — skipping Etsy scraping")
        return True  # Not an error, just not configured

    try:
        headers = {
            "x-api-key": settings.etsy_api_key,
        }

        params = {
            "keywords": keyword,
            "taxonomy_id": CLOTHING_TAXONOMY_ID,
            "limit": 100,
            "sort_on": "score",
            "sort_order": "desc",
        }

        resp = requests.get(ETSY_BASE_URL, headers=headers, params=params, timeout=20)

        if resp.status_code == 429:
            logger.warning(f"Etsy API rate limited for '{keyword}', will retry later")
            return False

        if resp.status_code != 200:
            logger.warning(f"Etsy API returned {resp.status_code} for '{keyword}': {resp.text[:200]}")
            return False

        data = resp.json()
        results = data.get("results", [])
        total_count = data.get("count", 0)

        if not results:
            logger.warning(f"No Etsy listings found for '{keyword}'")
            return True

        prices = []
        quantities = []
        for item in results:
            price_info = item.get("price", {})
            amount = price_info.get("amount")
            divisor = price_info.get("divisor", 100)
            if amount is not None:
                try:
                    price = float(amount) / float(divisor)
                    if 0 < price < 50000:
                        prices.append(price)
                except (ValueError, TypeError, ZeroDivisionError):
                    continue

            qty = item.get("quantity")
            if qty is not None:
                try:
                    quantities.append(int(qty))
                except (ValueError, TypeError):
                    pass

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()

        if prices:
            avg_price = sum(prices) / len(prices)
            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "etsy", "avg_price", avg_price, now),
            )

            # Price volatility (standard deviation)
            if len(prices) > 1:
                variance = sum((p - avg_price) ** 2 for p in prices) / (len(prices) - 1)
                volatility = variance ** 0.5
            else:
                volatility = 0.0

            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "etsy", "price_volatility", volatility, now),
            )

        # Store listing count (total from API, not just this page)
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "etsy", "sold_count", float(total_count), now),
        )

        # Store total available quantity
        if quantities:
            total_qty = sum(quantities)
            conn.execute(
                "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (keyword, "etsy", "available_quantity", float(total_qty), now),
            )

        conn.commit()
        conn.close()

        avg_str = f"${sum(prices)/len(prices):.2f}" if prices else "N/A"
        logger.info(f"Etsy scrape complete for '{keyword}': {total_count} total listings, avg {avg_str}")
        time.sleep(random.uniform(0.5, 1.5))
        return True

    except Exception as e:
        logger.error(f"Etsy scrape failed for '{keyword}': {e}")
        return False
