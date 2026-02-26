import base64
import time
import random
import logging
from datetime import datetime, timezone

import requests
from app.config import settings
from app.database import get_connection

logger = logging.getLogger(__name__)

# eBay OAuth token endpoint (sandbox if keys contain SBX, else production)
EBAY_AUTH_URL_PROD = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_AUTH_URL_SANDBOX = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

EBAY_BROWSE_URL_PROD = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_BROWSE_URL_SANDBOX = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"


def _is_sandbox() -> bool:
    return "SBX" in (settings.ebay_app_id or "")


EBAY_SCOPE_PROD = "https://api.ebay.com/oauth/api_scope"
EBAY_SCOPE_SANDBOX = "https://api.sandbox.ebay.com/oauth/api_scope"

_cached_token = {"token": None, "expires_at": 0}


def _get_oauth_token() -> str | None:
    """Get an eBay OAuth application access token using client credentials."""
    if not settings.ebay_app_id or not settings.ebay_cert_id:
        logger.warning("eBay API credentials not configured — skipping eBay scraping")
        return None

    # Check cache
    now = time.time()
    if _cached_token["token"] and _cached_token["expires_at"] > now + 60:
        return _cached_token["token"]

    try:
        credentials = base64.b64encode(
            f"{settings.ebay_app_id}:{settings.ebay_cert_id}".encode()
        ).decode()

        sandbox = _is_sandbox()
        auth_url = EBAY_AUTH_URL_SANDBOX if sandbox else EBAY_AUTH_URL_PROD
        scope = EBAY_SCOPE_SANDBOX if sandbox else EBAY_SCOPE_PROD

        resp = requests.post(
            auth_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
            data={
                "grant_type": "client_credentials",
                "scope": scope,
            },
            timeout=15,
        )
        resp.raise_for_status()

        data = resp.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 7200)

        _cached_token["token"] = token
        _cached_token["expires_at"] = now + expires_in

        logger.info("eBay OAuth token obtained successfully")
        return token

    except Exception as e:
        logger.error(f"Failed to get eBay OAuth token: {e}")
        return None


def scrape_ebay(keyword: str) -> bool:
    """Scrape eBay listings for a keyword using the Browse API. Returns True on success."""
    token = _get_oauth_token()
    if token is None:
        return True  # Not an error, just not configured

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "X-EBAY-C-ENDUSERCTX": "affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>",
        }

        # Search for items in Clothing, Shoes & Accessories (category 11450)
        params = {
            "q": keyword,
            "category_ids": "11450",
            "limit": "50",
            "sort": "newlyListed",
            "filter": "buyingOptions:{FIXED_PRICE|AUCTION}",
        }

        browse_url = EBAY_BROWSE_URL_SANDBOX if _is_sandbox() else EBAY_BROWSE_URL_PROD

        resp = requests.get(browse_url, headers=headers, params=params, timeout=20)

        if resp.status_code == 401:
            # Token expired, clear cache and retry once
            _cached_token["token"] = None
            token = _get_oauth_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(browse_url, headers=headers, params=params, timeout=20)

        if resp.status_code != 200:
            logger.warning(f"eBay Browse API returned {resp.status_code} for '{keyword}': {resp.text[:200]}")
            return False

        data = resp.json()
        items = data.get("itemSummaries", [])

        if not items:
            logger.warning(f"No eBay items found for '{keyword}'")
            return True

        prices = []
        images_to_store = []
        for item in items:
            price_info = item.get("price", {})
            value = price_info.get("value")
            item_price = None
            if value:
                try:
                    item_price = float(value)
                    if 0 < item_price < 50000:
                        prices.append(item_price)
                except (ValueError, TypeError):
                    pass

            image_url = item.get("image", {}).get("imageUrl")
            item_url = item.get("itemWebUrl")
            title = item.get("title")
            if image_url and len(images_to_store) < 6:
                images_to_store.append((keyword, "ebay", image_url, title, item_price, item_url))

        if not prices:
            logger.warning(f"No parseable eBay prices for '{keyword}'")
            return True

        now = datetime.now(timezone.utc).isoformat()
        avg_price = sum(prices) / len(prices)
        listing_count = len(items)

        # Price volatility (standard deviation)
        if len(prices) > 1:
            mean = avg_price
            variance = sum((p - mean) ** 2 for p in prices) / (len(prices) - 1)
            volatility = variance ** 0.5
        else:
            volatility = 0.0

        conn = get_connection()
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "ebay", "avg_price", avg_price, now),
        )
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "ebay", "sold_count", float(listing_count), now),
        )
        conn.execute(
            "INSERT INTO trend_data (keyword, source, metric, value, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (keyword, "ebay", "price_volatility", volatility, now),
        )

        for img in images_to_store:
            conn.execute(
                "INSERT OR IGNORE INTO trend_images (keyword, source, image_url, title, price, item_url) VALUES (?, ?, ?, ?, ?, ?)",
                img,
            )

        # Prune to 8 most recent images per keyword
        conn.execute(
            """DELETE FROM trend_images WHERE keyword = ? AND id NOT IN (
                SELECT id FROM trend_images WHERE keyword = ? ORDER BY scraped_at DESC LIMIT 8
            )""",
            (keyword, keyword),
        )

        conn.commit()
        conn.close()

        logger.info(f"eBay API scrape complete for '{keyword}': {listing_count} items, avg ${avg_price:.2f}")
        time.sleep(random.uniform(0.5, 1.5))
        return True

    except Exception as e:
        logger.error(f"eBay API scrape failed for '{keyword}': {e}")
        return False
