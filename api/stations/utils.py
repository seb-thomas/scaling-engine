import json
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


def verify_book_exists(title: str, author: str = "") -> dict:
    """
    Look up a book via Google Books API and return metadata.

    Used for enrichment (canonical title/author, cover, ISBN), not as a gate.
    Free, no API key required.

    Returns:
        dict with keys:
            - exists: bool (found a matching result)
            - title: str
            - author: str
            - cover_url: str or None (direct image URL)
            - isbn: str or None
    """
    not_found = {"exists": False, "title": title, "author": author, "cover_url": None, "isbn": None}
    try:
        query = f"{title} {author}".strip() if author else title
        params = {"q": query, "maxResults": 1}
        url = f"https://www.googleapis.com/books/v1/volumes?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(
            url, headers={"User-Agent": "RadioReads/1.0 (https://radioreads.fun)"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())

        items = data.get("items")
        if not items:
            return not_found

        info = items[0].get("volumeInfo", {})
        gb_title = info.get("title", "")
        gb_authors = info.get("authors", [])
        gb_author = gb_authors[0] if gb_authors else ""

        # Cover image: prefer thumbnail, upgrade to larger size
        cover_url = None
        image_links = info.get("imageLinks", {})
        if image_links.get("thumbnail"):
            # Replace zoom=1 with zoom=2 for a larger image
            cover_url = image_links["thumbnail"].replace("zoom=1", "zoom=2")

        # ISBN: prefer ISBN-13
        isbn = None
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_13":
                isbn = ident.get("identifier")
                break
            if ident.get("type") == "ISBN_10" and not isbn:
                isbn = ident.get("identifier")

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
