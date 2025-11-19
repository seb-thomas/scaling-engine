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


def fetch_book_cover(title: str, author: str = "") -> str:
    """
    Fetch book cover image URL from Open Library API.
    Returns empty string if no cover found.
    """
    try:
        # Search Open Library for the book
        search_query = title
        if author:
            search_query = f"{title} {author}"
        
        search_url = "https://openlibrary.org/search.json"
        params = {
            "q": search_query,
            "limit": 1,
            "fields": "isbn,cover_i"
        }
        
        url_with_params = f"{search_url}?{urllib.parse.urlencode(params)}"
        
        with urllib.request.urlopen(url_with_params, timeout=5) as response:
            data = json.loads(response.read().decode())
        
        if data.get("docs") and len(data["docs"]) > 0:
            book = data["docs"][0]
            
            # Try to get cover image
            if "cover_i" in book:
                cover_id = book["cover_i"]
                return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            
            # Fallback: try ISBN if available
            if "isbn" in book and book["isbn"]:
                isbn = book["isbn"][0] if isinstance(book["isbn"], list) else book["isbn"]
                return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        
        return ""
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
