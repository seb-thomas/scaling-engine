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
    Verify a book exists in Open Library and return its metadata.
    
    Uses the Open Library Search API to check if a book exists.
    See: https://openlibrary.org/dev/docs/api/covers
    
    Returns:
        dict with keys:
            - exists: bool
            - title: str (canonical title from Open Library)
            - author: str (canonical author from Open Library)  
            - cover_id: int or None (Open Library cover ID)
            - isbn: str or None (ISBN if available)
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
            "fields": "title,author_name,cover_i,isbn,first_publish_year"
        }
        
        url_with_params = f"{search_url}?{urllib.parse.urlencode(params)}"
        
        request = urllib.request.Request(
            url_with_params,
            headers={"User-Agent": "RadioReads/1.0 (https://radioreads.fun)"}
        )
        
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if data.get("docs") and len(data["docs"]) > 0:
            book = data["docs"][0]
            
            # Get author name (it's a list in the API)
            author_names = book.get("author_name", [])
            canonical_author = author_names[0] if author_names else ""
            
            # Get ISBN (it's a list)
            isbns = book.get("isbn", [])
            isbn = isbns[0] if isbns else None
            
            return {
                "exists": True,
                "title": book.get("title", title),
                "author": canonical_author,
                "cover_id": book.get("cover_i"),
                "isbn": isbn,
                "first_publish_year": book.get("first_publish_year"),
            }
        
        return {"exists": False, "title": title, "author": author, "cover_id": None, "isbn": None}
        
    except Exception as e:
        logger.warning(f"Failed to verify book '{title}': {e}")
        return {"exists": False, "title": title, "author": author, "cover_id": None, "isbn": None}


def fetch_book_cover(title: str, author: str = "") -> str:
    """
    Fetch book cover image URL from Open Library API.
    
    Uses the Open Library Covers API:
    https://openlibrary.org/dev/docs/api/covers
    
    Returns empty string if no cover found.
    """
    try:
        # First verify the book exists and get its cover_id
        book_info = verify_book_exists(title, author)
        
        if not book_info["exists"]:
            return ""
        
        # Use cover_id if available (most reliable)
        if book_info["cover_id"]:
            return f"https://covers.openlibrary.org/b/id/{book_info['cover_id']}-L.jpg"
        
        # Fallback to ISBN
        if book_info["isbn"]:
            return f"https://covers.openlibrary.org/b/isbn/{book_info['isbn']}-L.jpg"
        
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
