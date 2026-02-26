import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

from app.database import get_connection

logger = logging.getLogger(__name__)

# Patterns that indicate a Pinterest "idea pin" / blog post collage rather than a clean photo
_ARTICLE_PATTERNS = re.compile(
    r'^\d+\s'                           # starts with a number ("8 Luxury...", "10 Ways...")
    r'|how\s+to\b'                      # "how to style"
    r'|\bways?\s+to\b'                  # "ways to wear"
    r'|\btips?\b'                       # "tips for"
    r'|\bguide\b'                       # "ultimate guide"
    r'|\bmastering\b'                   # "mastering the art of"
    r'|\btutorial\b'                    # "tutorial"
    r'|\byou\s+need\b'                  # "everything you need"
    r'|\bbrands?\b'                     # "best brands"
    r'|\.com\b'                         # contains a domain ("gooseberryintimates.com")
    r'|\binspo\s+board\b'               # "inspo board"
    r'|\bideas\b'                       # "outfit ideas", "style ideas"
    r'|\bessentials\b'                  # "wardrobe essentials"
    r'|\bwardrobe\b'                    # "build a wardrobe"
    r'|\bbuild\s+a\b'                   # "build a..."
    r'|\boutfit\s+ideas\b'              # "outfit ideas"
    r'|\blook\s+book\b'                 # "look book"
    r'|\blookbook\b'                    # "lookbook"
    r'|\bcheat\s+sheet\b'               # "cheat sheet"
    r'|\binspiration\s+board\b'          # "inspiration board"
    r'|\baction\s+item\b'               # Pinterest UI artifact "Action Item Rep Preview Image"
    r'|\bpreview\s+image\b'             # "Preview Image" UI artifacts
    r'|\bcheck\s+out\b'                 # "Check out these..."
    r'|\baesthetic\s+refers\b',         # "aesthetic refers to..." (description text)
    re.IGNORECASE,
)


def _is_article_pin(title: str) -> bool:
    """Return True if the pin title looks like a blog/listicle article rather than a photo."""
    if not title:
        return False
    return bool(_ARTICLE_PATTERNS.search(title))


def scrape_pinterest_images(keyword: str) -> list:
    """Scrape Pinterest search for fashion images using Playwright.
    Stores results in trend_images and returns the list."""
    images = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()

            # Block fonts, media, and tracking to speed up load
            page.route(
                "**/*.{woff,woff2,ttf,otf,mp4,webm,ogg,mp3}",
                lambda route: route.abort(),
            )

            url = f"https://www.pinterest.com/search/pins/?q={quote_plus(keyword + ' fashion')}&rs=typed"
            try:
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
            except Exception:
                browser.close()
                return []

            # Bail out if redirected to login
            if "login" in page.url or "signup" in page.url:
                logger.warning(f"Pinterest redirected to login for '{keyword}'")
                browser.close()
                return []

            # Wait for pin images from Pinterest CDN
            try:
                page.wait_for_selector("img[src*='i.pinimg.com']", timeout=10000)
            except Exception:
                browser.close()
                return []

            # Scroll once to load more pins
            page.evaluate("window.scrollBy(0, 600)")
            page.wait_for_timeout(1500)

            img_elements = page.query_selector_all("img[src*='i.pinimg.com']")

            seen_urls = set()
            candidates = []
            for img in img_elements:
                src = img.get_attribute("src") or ""
                if not src or src in seen_urls:
                    continue

                # Only accept actual pin images — must have a large-enough dimension in the URL
                # e.g. /236x/, /474x/, /564x/, /736x/  — skip 60x60, 75x75 avatars
                size_match = re.search(r'/(\d+)x/', src)
                if not size_match or int(size_match.group(1)) < 200:
                    continue

                # Upgrade to larger size for better quality
                for small, large in [("/236x/", "/564x/"), ("/474x/", "/564x/")]:
                    src = src.replace(small, large)

                alt = img.get_attribute("alt") or ""

                # Skip images with no alt text — real fashion photos always have descriptions
                if not alt.strip():
                    continue

                # Skip article/listicle collage pins
                if _is_article_pin(alt):
                    continue

                # Get the closest anchor link for the pin
                item_url = img.evaluate(
                    "el => el.closest('a') ? el.closest('a').href : null"
                )

                seen_urls.add(src)
                candidates.append({
                    "keyword": keyword,
                    "source": "pinterest",
                    "image_url": src,
                    "title": alt[:200] if alt else None,
                    "price": None,
                    "item_url": item_url,
                })

                if len(candidates) >= 8:
                    break

            images = candidates[:6]

            browser.close()

    except Exception as e:
        logger.error(f"Pinterest image scrape failed for '{keyword}': {e}")
        return []

    if images:
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        for img in images:
            conn.execute(
                "INSERT OR IGNORE INTO trend_images "
                "(keyword, source, image_url, title, price, item_url, scraped_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (img["keyword"], img["source"], img["image_url"],
                 img["title"], img["price"], img["item_url"], now),
            )
        # Prune to 8 most recent per keyword
        conn.execute(
            """DELETE FROM trend_images WHERE keyword = ? AND id NOT IN (
                SELECT id FROM trend_images WHERE keyword = ?
                ORDER BY scraped_at DESC LIMIT 8
            )""",
            (keyword, keyword),
        )
        conn.commit()
        conn.close()
        logger.info(f"Pinterest: stored {len(images)} images for '{keyword}'")

    return images
