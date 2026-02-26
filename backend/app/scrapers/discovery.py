import json
import logging
import math
import re
import time
from collections import Counter

from app.config import settings
from app.database import get_connection
from app.scrapers.reddit import discover_trending_keywords as reddit_discover
from app.scrapers.depop import discover_trending_keywords as depop_discover

logger = logging.getLogger(__name__)

# Common words to filter out from discovery
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "my", "your", "his", "her", "its", "our", "their", "this", "that",
    "these", "those", "i", "me", "we", "you", "he", "she", "it", "they",
    "what", "which", "who", "whom", "whose", "anyone", "someone",
    "look", "looking", "got", "get", "new", "like", "help", "want",
    "think", "know", "find", "anyone", "advice", "opinion", "thoughts",
}


def find_similar_keyword(keyword: str, conn, confirm: bool = True) -> str | None:
    """Use Claude to check if any existing tracked keyword refers to the same fashion trend.
    Returns the matching existing keyword, or None if no duplicate found.
    Falls back to None (allow the keyword) if the API key is not set or the call fails.
    confirm=True (default): requires a second confirmation call before returning a match (for auto-merging).
    confirm=False: trusts the first call result (for user-facing suggestions where the user decides)."""
    if not settings.anthropic_api_key:
        return None

    rows = conn.execute(
        "SELECT keyword FROM keywords WHERE status != 'inactive'"
    ).fetchall()
    existing = [row["keyword"] for row in rows if row["keyword"] != keyword]

    if not existing:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        keywords_list = "\n".join(f"- {k}" for k in existing)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    f'New fashion trend keyword: "{keyword}"\n\n'
                    f"Existing tracked keywords:\n{keywords_list}\n\n"
                    "Is the new keyword an EXACT SYNONYM of any existing keyword — meaning two different names "
                    "for the literally identical item or trend? "
                    "Examples of true synonyms: 'draped top' = 'draped top blouse', 'barrel leg jeans' = 'barrel jeans'. "
                    "Distinct named aesthetics, styles, or movements are NEVER duplicates, even if they share "
                    "visual overlap or mood (e.g. 'goth' ≠ 'dark academia', 'quiet luxury' ≠ 'old money', "
                    "'cottagecore' ≠ 'boho', 'minimalism' ≠ 'quiet luxury'). "
                    "Only reply with a matching keyword if you are certain they are two names for the exact same thing. "
                    "When in doubt, reply none. "
                    "Reply with ONLY the exact matching keyword from the list above, or reply with ONLY the word: none"
                ),
            }],
        )

        reply = response.content[0].text.strip().lower()
        if reply == "none":
            return None

        # Match reply against existing keywords (case-insensitive)
        matched = None
        for k in existing:
            if k.lower() == reply:
                matched = k
                break

        if not matched:
            return None

        if not confirm:
            return matched  # Caller (user suggestion UI) will let the user decide

        # Second confirmation: verify the match is truly an exact synonym, not just related
        confirm_resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": (
                    f'Are "{keyword}" and "{matched}" literally two different names for the '
                    f"exact same fashion trend or item — not just related, similar, or overlapping, "
                    f"but the exact same thing with different wording? "
                    f"(e.g. 'draped top' and 'draped blouse' = YES. "
                    f"'goth' and 'dark academia' = NO. 'quiet luxury' and 'old money' = NO.) "
                    f"Answer with ONLY: YES or NO"
                ),
            }],
        )
        confirmed = confirm_resp.content[0].text.strip().upper()
        if confirmed == "YES":
            return matched

        return None

    except Exception as e:
        logger.warning(f"Claude similarity check failed for '{keyword}': {e}")
        return None


def classify_keyword_scale(keyword: str) -> str:
    """Use Claude to classify a keyword as 'macro' or 'micro' fashion trend.
    Macro = broad aesthetic, movement, era, or style philosophy.
    Micro = specific garment, accessory, material, or item.
    Falls back to 'macro' on failure."""
    if not settings.anthropic_api_key:
        return "macro"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": (
                    f'Fashion keyword: "{keyword}"\n\n'
                    "Classify as MACRO or MICRO using these criteria:\n\n"
                    "MACRO = long-term (years/decades), broad societal or industry shift, "
                    "driven by deep cultural value changes, adopted mainstream. "
                    "Examples: quiet luxury, old money, gorpcore, maximalism, sustainability, minimalism, utility wear.\n\n"
                    "MICRO = short-lived (weeks/months), niche, accelerated by social media virality, "
                    "fades quickly, adopted by trend-conscious minority. "
                    "Examples: barbiecore, mob wife aesthetic, cottagecore, dark academia, blokecore, "
                    "tenniscore, ballet flats, cherry red, barrel-leg jeans.\n\n"
                    "Key question: Is this a lasting cultural shift (macro) or a social-media-driven fad (micro)?\n"
                    "Reply with ONLY one word: macro or micro"
                ),
            }],
        )
        result = response.content[0].text.strip().lower()
        return "micro" if "micro" in result else "macro"
    except Exception as e:
        logger.warning(f"Scale classification failed for '{keyword}': {e}")
        return "macro"


def backfill_scale_classifications(force: bool = False):
    """Classify all keywords that don't have a scale assigned yet. Runs at startup.
    Pass force=True to re-classify all keywords regardless of existing scale."""
    conn = get_connection()
    query = "SELECT keyword FROM keywords WHERE status != 'inactive'" if force else \
            "SELECT keyword FROM keywords WHERE scale IS NULL AND status != 'inactive'"
    rows = conn.execute(query).fetchall()
    conn.close()

    keywords = [r["keyword"] for r in rows]
    if not keywords:
        return

    logger.info(f"Backfilling scale classifications for {len(keywords)} keywords")
    for keyword in keywords:
        scale = classify_keyword_scale(keyword)
        conn = get_connection()
        conn.execute("UPDATE keywords SET scale = ? WHERE keyword = ?", (scale, keyword))
        conn.commit()
        conn.close()
        logger.info(f"Scale: '{keyword}' → {scale}")
        time.sleep(0.3)


def refine_scale_classifications():
    """Periodically review keyword scale classifications using statistical signals from
    accumulated data. Only overrides the current classification when evidence is strong.

    Signals used:
      - CV (coefficient of variation) of search volume: high = volatile = micro
      - Variance of composite score across time windows (7/14/30/60/90d): high = micro

    Thresholds are intentionally conservative — both signals must agree before
    overriding, and a minimum of 5 search-volume points is required.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT keyword, scale FROM keywords WHERE status = 'active'"
    ).fetchall()
    conn.close()

    updates = 0
    skipped = 0

    for row in rows:
        keyword = row["keyword"]
        current_scale = row["scale"] or "macro"

        conn = get_connection()

        # All historical search volume points for this keyword
        sv_rows = conn.execute(
            "SELECT value FROM trend_data WHERE keyword = ? AND metric = 'search_volume' ORDER BY recorded_at",
            (keyword,),
        ).fetchall()

        # Composite scores across all stored time windows
        score_rows = conn.execute(
            "SELECT composite_score FROM trend_scores WHERE keyword = ? AND composite_score IS NOT NULL",
            (keyword,),
        ).fetchall()

        conn.close()

        sv_values = [r["value"] for r in sv_rows]
        scores = [r["composite_score"] for r in score_rows]

        # Require sufficient data before trusting the statistics
        if len(sv_values) < 5 or len(scores) < 3:
            skipped += 1
            continue

        # Coefficient of variation of search volume
        mean_sv = sum(sv_values) / len(sv_values)
        if mean_sv == 0:
            skipped += 1
            continue
        std_sv = math.sqrt(sum((v - mean_sv) ** 2 for v in sv_values) / len(sv_values))
        cv = std_sv / mean_sv

        # Variance of composite score across time windows
        mean_score = sum(scores) / len(scores)
        score_variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Strong micro: high volatility confirmed by both signals
        if cv > 0.65 and score_variance > 1500:
            new_scale = "micro"
        # Strong macro: very stable confirmed by both signals
        elif cv < 0.15 and score_variance < 150:
            new_scale = "macro"
        else:
            # Evidence is ambiguous — trust the existing classification
            continue

        if new_scale != current_scale:
            conn = get_connection()
            conn.execute("UPDATE keywords SET scale = ? WHERE keyword = ?", (new_scale, keyword))
            conn.commit()
            conn.close()
            logger.info(
                f"Scale refined: '{keyword}' {current_scale} → {new_scale} "
                f"(CV={cv:.2f}, score_var={score_variance:.0f}, n={len(sv_values)} points)"
            )
            updates += 1

    logger.info(
        f"Scale refinement complete: {updates} updated, {skipped} skipped (insufficient data)"
    )


def load_seed_keywords():
    """Load seed keywords from JSON file into the keywords table."""
    try:
        with open(settings.seed_keywords_path, "r") as f:
            seeds = json.load(f)

        conn = get_connection()
        for keyword in seeds:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO keywords (keyword, source, status) VALUES (?, 'seed', 'active')",
                    (keyword.lower().strip(),),
                )
            except Exception:
                pass
        conn.commit()
        conn.close()
        logger.info(f"Loaded {len(seeds)} seed keywords")
    except FileNotFoundError:
        logger.warning(f"Seed keywords file not found: {settings.seed_keywords_path}")
    except Exception as e:
        logger.error(f"Failed to load seed keywords: {e}")


def get_active_keywords() -> list[str]:
    """Get all active keywords from the database."""
    conn = get_connection()
    rows = conn.execute("SELECT keyword FROM keywords WHERE status = 'active'").fetchall()
    conn.close()
    return [row["keyword"] for row in rows]


def _extract_fashion_terms(titles: list[str]) -> list[str]:
    """Extract potential fashion keywords from post titles using bigram/trigram frequency."""
    all_words = []
    for title in titles:
        # Clean and tokenize
        words = re.findall(r"[a-z]+", title.lower())
        words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        all_words.extend(words)

        # Also extract bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            all_words.append(bigram)

    # Count frequencies
    counts = Counter(all_words)
    # Return terms that appear at least 3 times
    return [term for term, count in counts.most_common(20) if count >= 3]


def run_discovery():
    """Run auto-discovery: scrape Reddit and Depop for new trending fashion terms."""
    logger.info("Running keyword auto-discovery...")

    # Gather candidate titles/terms
    reddit_titles = reddit_discover()
    depop_terms = depop_discover()

    # Extract fashion terms from Reddit titles
    reddit_candidates = _extract_fashion_terms(reddit_titles)

    # Combine all candidates
    all_candidates = set(reddit_candidates + depop_terms)

    # Get existing keywords to avoid duplicates
    conn = get_connection()
    existing = conn.execute("SELECT keyword FROM keywords").fetchall()
    existing_set = {row["keyword"] for row in existing}

    new_count = 0
    for candidate in all_candidates:
        candidate = candidate.lower().strip()
        if not candidate or len(candidate) <= 2:
            continue
        if candidate in existing_set:
            continue
        similar = find_similar_keyword(candidate, conn)
        if similar:
            logger.debug(f"Discovery: skipping '{candidate}' — similar to existing '{similar}'")
            continue
        conn.execute(
            "INSERT OR IGNORE INTO keywords (keyword, source, status) VALUES (?, 'auto_discovered', 'pending_review')",
            (candidate,),
        )
        existing_set.add(candidate)
        new_count += 1

    conn.commit()
    conn.close()

    logger.info(f"Auto-discovery complete: {new_count} new candidates added for review")
    return new_count
