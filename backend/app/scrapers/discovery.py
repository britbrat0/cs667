import json
import logging
import re
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
        if candidate and candidate not in existing_set and len(candidate) > 2:
            conn.execute(
                "INSERT OR IGNORE INTO keywords (keyword, source, status) VALUES (?, 'auto_discovered', 'pending_review')",
                (candidate,),
            )
            new_count += 1

    conn.commit()
    conn.close()

    logger.info(f"Auto-discovery complete: {new_count} new candidates added for review")
    return new_count
