import json
import os
import urllib.request
import urllib.parse
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from .models import Episode, Phrase

logger = get_task_logger(__name__)


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
    """Make a request to Google Books API."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "RadioReads/1.0 (https://radioreads.fun)"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


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
        params = {"q": query, "maxResults": 1}
        if api_key:
            params["key"] = api_key
        search_url = f"https://www.googleapis.com/books/v1/volumes?{urllib.parse.urlencode(params)}"
        data = _gb_request(search_url)

        items = data.get("items")
        if not items:
            return not_found

        info = items[0].get("volumeInfo", {})
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

        # Step 2: Get cover URL via volume detail endpoint (tokenised URLs
        # that work from server IPs). Falls back to search thumbnails.
        cover_url = None
        vol_id = items[0].get("id")
        if api_key and vol_id:
            try:
                vol_url = f"https://www.googleapis.com/books/v1/volumes/{vol_id}?key={api_key}"
                vol_data = _gb_request(vol_url)
                vol_links = vol_data.get("volumeInfo", {}).get("imageLinks", {})
                # Prefer medium (~575px wide), fall back through sizes
                cover_url = (
                    vol_links.get("medium")
                    or vol_links.get("large")
                    or vol_links.get("small")
                    or vol_links.get("thumbnail")
                )
            except Exception as e:
                logger.debug(f"Volume detail fetch failed for {vol_id}: {e}")

        # Fallback: use search thumbnail (may 403 from server IPs)
        if not cover_url:
            image_links = info.get("imageLinks", {})
            cover_url = image_links.get("thumbnail")

        return {
            "exists": True,
            "title": gb_title,
            "author": gb_author,
            "cover_url": cover_url,
            "isbn": isbn,
        }
    except Exception as e:
        logger.warning(f"Google Books lookup failed for '{title}': {e}")
        return not_found


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
