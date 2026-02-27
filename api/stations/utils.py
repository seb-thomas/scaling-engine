import json
import os
import time
import urllib.request
import urllib.parse
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from .models import Episode, Phrase

logger = get_task_logger(__name__)

# Rate limiting for Google Books API
_last_gb_request_time = 0.0
_GB_MIN_INTERVAL = 1.0  # minimum seconds between requests
_gb_cooldown_until = 0.0  # when set, skip GB calls until this monotonic time
_GB_COOLDOWN_SECONDS = 43200  # 12-hour cooldown after a 429


class GoogleBooksRateLimited(Exception):
    """Raised when Google Books API returns 429 and retries are exhausted."""
    pass


def contains_keywords(episode_id):
    try:
        episode = Episode.objects.get(pk=episode_id)

        # Get keyword list once instead of creating new Phrase instance
        keyword_list = list(Phrase.objects.values_list("text", flat=True))

        if not keyword_list:
            logger.warning(f"No keywords configured. Episode {episode_id} cannot be checked.")
            return False

        if any(keyword in episode.title for keyword in keyword_list):
            episode.has_book = True
            episode.save(update_fields=["has_book"])
            logger.info(f"Episode {episode_id} '{episode.title}' contains book keywords")
            return True
        else:
            logger.debug(f"Episode {episode_id} '{episode.title}' has no book keywords")
            return False

    except Episode.DoesNotExist:
        logger.warning(f"Episode {episode_id} does not exist")
        return False
    except DatabaseError as e:
        logger.error(f"Database error checking episode {episode_id}: {e}")
        raise  # Re-raise to trigger Celery retry


def _gb_api_key():
    return os.environ.get("GOOGLE_BOOKS_API_KEY", "")


def _gb_request(url):
    """Make a request to Google Books API with rate limiting and 429 cooldown."""
    global _last_gb_request_time, _gb_cooldown_until

    # If in cooldown after a recent 429 storm, skip immediately
    now = time.monotonic()
    if now < _gb_cooldown_until:
        remaining = int(_gb_cooldown_until - now)
        raise GoogleBooksRateLimited(
            f"Google Books API in cooldown ({remaining}s remaining)"
        )

    # Enforce minimum interval between requests
    elapsed = now - _last_gb_request_time
    if elapsed < _GB_MIN_INTERVAL:
        time.sleep(_GB_MIN_INTERVAL - elapsed)
    _last_gb_request_time = time.monotonic()

    req = urllib.request.Request(
        url, headers={"User-Agent": "RadioReads/1.0 (https://radioreads.fun)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            # Rate limited — stop immediately, enter 12-hour cooldown
            _gb_cooldown_until = time.monotonic() + _GB_COOLDOWN_SECONDS
            logger.warning(
                f"Google Books 429 rate limited, entering {_GB_COOLDOWN_SECONDS // 3600}h cooldown"
            )
            raise GoogleBooksRateLimited(str(e)) from e
        raise


def verify_book_exists(title: str, author: str = "") -> dict:
    """
    Look up a book via Google Books API and return metadata.

    Used for enrichment (canonical title/author, cover, ISBN), not as a gate.
    With an API key, fetches volume detail to get tokenised cover URLs
    that work from server IPs.

    Returns:
        dict with keys:
            - exists: bool (found a matching result)
            - title: str
            - author: str
            - cover_url: str or None (direct image URL)
            - isbn: str or None
    """
    not_found = {"exists": False, "title": title, "author": author, "cover_url": None, "isbn": None}
    api_key = _gb_api_key()
    try:
        # Step 1: Search using intitle/inauthor for precise matching
        if author:
            query = f"intitle:{title} inauthor:{author}"
        else:
            query = title
        # Fetch several results so we can pick the edition with the best cover
        params = {"q": query, "maxResults": 5}
        if api_key:
            params["key"] = api_key
        search_url = f"https://www.googleapis.com/books/v1/volumes?{urllib.parse.urlencode(params)}"
        data = _gb_request(search_url)

        items = data.get("items")
        if not items:
            return not_found

        # Step 2: Among the results, find the one with the best cover.
        # Cap at large (~800px) — extraLarge is overkill for rendered sizes.
        _SIZE_RANK = {"large": 4, "medium": 3, "small": 2, "thumbnail": 1, "smallThumbnail": 0}

        # Use first result for metadata (most relevant match)
        info = items[0].get("volumeInfo", {})

        best_cover_url = None
        best_cover_score = -1

        if api_key:
            for item in items:
                vol_id = item.get("id")
                if not vol_id:
                    continue
                try:
                    vol_url = f"https://www.googleapis.com/books/v1/volumes/{vol_id}?key={api_key}"
                    vol_data = _gb_request(vol_url)
                    vol_links = vol_data.get("volumeInfo", {}).get("imageLinks", {})
                    # Score this volume by its best available size
                    for size_name in ("large", "medium", "small", "thumbnail"):
                        if size_name in vol_links:
                            score = _SIZE_RANK[size_name]
                            if score > best_cover_score:
                                best_cover_score = score
                                best_cover_url = vol_links[size_name]
                            break  # only care about the best size this volume offers
                except Exception as e:
                    logger.debug(f"Volume detail fetch failed for {vol_id}: {e}")
        gb_title = info.get("title", "")
        gb_authors = info.get("authors", [])
        gb_author = gb_authors[0] if gb_authors else ""

        # ISBN: prefer ISBN-13
        isbn = None
        isbn_10 = None
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_13":
                isbn = ident.get("identifier")
            elif ident.get("type") == "ISBN_10":
                isbn_10 = ident.get("identifier")
        isbn = isbn or isbn_10

        # Fallback: use search thumbnail only without API key.
        # With an API key, volume detail returns tokenised URLs; search
        # thumbnails are untokenised and 403 from server/datacenter IPs.
        if not best_cover_url and not api_key:
            image_links = info.get("imageLinks", {})
            best_cover_url = image_links.get("thumbnail")

        return {
            "exists": True,
            "title": gb_title,
            "author": gb_author,
            "cover_url": best_cover_url,
            "isbn": isbn,
        }
    except GoogleBooksRateLimited:
        raise  # let caller handle rate limiting differently from other errors
    except Exception as e:
        logger.warning(f"Google Books lookup failed for '{title}': {e}")
        not_found["error"] = str(e)[:200]
        return not_found


def _open_library_cover_url(title: str, author: str = "") -> str:
    """
    Look up a cover image via Open Library as a fallback.
    Returns a direct image URL (L size) or empty string.
    """
    try:
        params = {"title": title, "limit": 1}
        if author:
            params["author"] = author
        url = f"https://openlibrary.org/search.json?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "RadioReads/1.0 (https://radioreads.fun)"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        docs = data.get("docs", [])
        if docs and docs[0].get("cover_i"):
            cover_id = docs[0]["cover_i"]
            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except Exception as e:
        logger.debug(f"Open Library cover lookup failed for '{title}': {e}")
    return ""


def fetch_book_cover(title: str, author: str = "") -> str:
    """
    Fetch book cover image URL via Google Books API.
    Returns empty string if no cover found.
    """
    try:
        book_info = verify_book_exists(title, author)
        return book_info.get("cover_url") or ""
    except Exception as e:
        logger.warning(f"Failed to fetch cover for '{title}': {e}")
        return ""


def generate_bookshop_affiliate_url(title: str, author: str = "") -> str:
    """
    Generate Bookshop.org affiliate search URL for a book.
    Returns a URL that searches Bookshop.org for the book with affiliate tracking.
    """
    from django.conf import settings
    
    import urllib.parse
    
    # Build search query
    search_terms = [title]
    if author:
        search_terms.append(author)
    
    query = " ".join(search_terms)
    encoded_query = urllib.parse.quote_plus(query)
    
    # Get affiliate ID from settings (defaults to 16640)
    affiliate_id = getattr(settings, 'BOOKSHOP_AFFILIATE_ID', '16640')
    
    # Bookshop.org UK search URL with affiliate tracking
    return f"https://uk.bookshop.org/search?q={encoded_query}&aid={affiliate_id}"
