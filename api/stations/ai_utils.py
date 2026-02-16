"""
AI-powered book extraction using Claude API.

This module uses Anthropic's Claude API to intelligently extract book mentions
from episode titles and descriptions, replacing simple keyword matching.
"""

import os
import logging
import json
import tempfile
import urllib.request
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError
from django.core.files import File

logger = logging.getLogger(__name__)


def _parse_date(date_text: str) -> Optional[datetime]:
    """
    Parse date text from BBC episode pages.

    Expected formats:
    - "24 Nov 2025"
    - "10 November 2025"
    - "Radio 4, 24 Nov 2025, 29 mins" (with extra text)
    """
    if not date_text:
        return None

    # Clean the date text
    clean_date = date_text.split(",")[-1].strip() if "," in date_text else date_text.strip()
    clean_date = clean_date.split("·")[0].strip() if "·" in clean_date else clean_date

    # Try common BBC date formats
    date_formats = [
        "%d %b %Y",      # "24 Nov 2025"
        "%d %B %Y",      # "24 November 2025"
        "%Y-%m-%d",      # "2025-11-24"
        "%d/%m/%Y",      # "24/11/2025"
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(clean_date, fmt)
        except ValueError:
            continue

    logger.debug(f"Could not parse date: '{date_text}' (cleaned: '{clean_date}')")
    return None


class BookExtractor:
    """Extracts book information from text using Claude AI."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the book extractor.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning(
                "No Anthropic API key provided. AI extraction will be disabled."
            )
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

    def extract_books(self, text: str, max_retries: int = 2) -> Dict:
        """
        Extract book information from text using Claude.

        Args:
            text: The text to analyze (episode title, description, etc.)
            max_retries: Number of times to retry on API errors

        Returns:
            Dict with keys:
                - has_book: bool
                - books: List[Dict] with title, author (optional), confidence
                - reasoning: str explaining the decision
        """
        if not self.client:
            logger.error("Claude client not initialized. Skipping AI extraction.")
            return {
                "has_book": False,
                "books": [],
                "reasoning": "API key not configured",
            }

        prompt = f"""We collect books discussed, reviewed, or interviewed about on radio. Not books mentioned only in adaptation context (film, theatre, TV, musical, play).

Analyze this BBC radio episode text. Extract only books that are the subject of the segment.

Episode text: "{text}"

Rules:
- Do not infer from author names alone. "Tom Stoppard" or "Anne Brontë biographer" without a book discussion = no extraction.
- Require author + book title, OR explicit book-type words: "book", "novel", "short story collection", "autobiography", "memoir".
- "Thriller" or "comedy" alone = often TV/film, not books. We describe books as "thrilling" or "hilarious". Do not extract titles that could be film/TV unless there is author + book signal (e.g. "the contemporary thriller Lurker" = TV show, NOT a book).
- Exclude when context is adaptation, play, or musical. Signals: adaptation, adapted, film, movie, director, theatre, stage, screen, play, musical, transformed into, starring, choreographer, BBC adaptation, RSC production, West End. "Play" = theatre, not a book. "Musical based on [book]" = segment is about the musical, not the book.
- Each book description must match the book title; do not mix descriptions between books.

INCLUDE examples: "Mark Haddon's autobiography Leaving Home"; "Eric Schlosser's book Fast Food Nation... talks to the author"; "George Saunders' new book, Vigil"; prize announcements with author + book; "short story collection by Joy Williams"; "have read James Meek's book Your Life Without Me".

EXCLUDE examples: "Anne Brontë biographer" (no book); "thriller Lurker" (TV show); "BBC adaptation of Lord of the Flies"; "A Christmas Carol... transformed into hip hop dance"; "her new play My Brother's a Genius"; "RSC's new production of Cyrano de Bergerac"; "musical based on Rachel's hit book The Unlikely Pilgrimage of Harold Fry" (context is the musical).

Return JSON only:
{{
    "has_book": true/false,
    "books": [
        {{
            "title": "Book Title",
            "author": "Author Name",
            "description": "A brief, engaging description of what the book is about",
            "confidence": 0.95
        }}
    ],
    "reasoning": "Brief explanation of your decision"
}}

Confidence 0.0-1.0 (0.8+ for clear mentions). Return ONLY valid JSON, no additional text."""

        for attempt in range(max_retries + 1):
            try:
                message = self.client.messages.create(
                    model="claude-3-haiku-20240307",  # Fast and cost-effective
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from response
                response_text = message.content[0].text.strip()

                # Parse JSON response
                result = json.loads(response_text)

                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError("Response is not a dict")
                if "has_book" not in result:
                    raise ValueError("Response missing 'has_book' field")

                # Ensure required fields
                result.setdefault("books", [])
                result.setdefault("reasoning", "No reasoning provided")

                logger.info(
                    f"AI extraction result: has_book={result['has_book']}, "
                    f"books_found={len(result['books'])}"
                )

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.debug(f"Response was: {response_text[:200]}")
                if attempt < max_retries:
                    continue
                return {"has_book": False, "books": [], "reasoning": "JSON parse error"}

            except (APIError, APITimeoutError, RateLimitError) as e:
                logger.error(
                    f"Claude API error (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                if attempt < max_retries:
                    continue
                return {
                    "has_book": False,
                    "books": [],
                    "reasoning": f"API error: {str(e)}",
                }

            except Exception as e:
                logger.exception(f"Unexpected error in AI extraction: {e}")
                return {"has_book": False, "books": [], "reasoning": f"Error: {str(e)}"}

        return {"has_book": False, "books": [], "reasoning": "Max retries exceeded"}

    def is_available(self) -> bool:
        """Check if the AI extractor is available (API key configured)."""
        return self.client is not None


def download_and_save_cover(book, cover_url: str) -> bool:
    """
    Download a cover image from URL and save it to the book's ImageField.

    Args:
        book: Book model instance
        cover_url: URL of the cover image

    Returns:
        True if successful, False otherwise
    """
    if not cover_url:
        return False

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            request = urllib.request.Request(
                cover_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; RadioReads/1.0)"}
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                tmp_file.write(response.read())
                tmp_path = tmp_file.name

        filename = f"{book.slug}.jpg"
        with open(tmp_path, "rb") as f:
            book.cover_image.save(filename, File(f), save=True)

        os.unlink(tmp_path)
        logger.info(f"Downloaded and saved cover for '{book.title}'")
        return True

    except Exception as e:
        logger.error(f"Failed to download cover for '{book.title}': {e}")
        return False


# Singleton instance
_extractor = None


def get_book_extractor() -> BookExtractor:
    """Get or create the global BookExtractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = BookExtractor()
    return _extractor


def extract_books_from_episode(episode_id: int) -> Dict:
    """
    Extract book information from an episode using AI.

    Args:
        episode_id: Episode primary key

    Returns:
        Dict with extraction results
    """
    from .models import Episode

    try:
        episode = Episode.objects.get(pk=episode_id)
        extractor = get_book_extractor()

        if not extractor.is_available():
            logger.warning("AI extraction not available. Please set ANTHROPIC_API_KEY.")
            return {"has_book": False, "books": [], "reasoning": "API not configured"}

        # Extract from raw_data if available, otherwise fall back to title
        text_to_analyze = episode.title
        if hasattr(episode, "raw_data") and episode.raw_data:
            # Combine title and description from raw_data for better context
            scraped_data = episode.raw_data.scraped_data
            raw_title = scraped_data.get("title", episode.title)
            raw_description = scraped_data.get("description", "")
            text_to_analyze = f"{raw_title}. {raw_description}".strip()

            # Parse and update aired_at date if not already set
            if not episode.aired_at:
                date_text = scraped_data.get("date_text")
                if date_text:
                    parsed_date = _parse_date(date_text)
                    if parsed_date:
                        episode.aired_at = parsed_date
                        episode.save(update_fields=["aired_at"])
                        logger.info(f"Parsed aired_at date for episode {episode_id}: {parsed_date}")

        result = extractor.extract_books(text_to_analyze)

        # Persist extraction result for evaluation (reasoning, books list)
        if hasattr(episode, "raw_data") and episode.raw_data:
            episode.raw_data.extraction_result = {
                "has_book": result.get("has_book", False),
                "reasoning": result.get("reasoning", ""),
                "books": result.get("books", []),
            }
            episode.raw_data.save(update_fields=["extraction_result"])

        # Update episode and save books if found
        if result["has_book"]:
            if not episode.has_book:
                episode.has_book = True
                episode.save(update_fields=["has_book"])
                logger.info(f"Episode {episode_id} marked as has_book=True by AI")

            # Save extracted books to database
            from .models import Book
            from .utils import fetch_book_cover, verify_book_exists

            logger.info(
                f"Processing {len(result.get('books', []))} potential books for episode {episode_id}"
            )
            for book_data in result.get("books", []):
                book_title = book_data.get("title", "").strip()
                book_author = book_data.get("author", "").strip()
                
                # Skip invalid titles
                if not book_title or book_title.upper() in ["N/A", "NA", "UNKNOWN", "TBD", "TBA"]:
                    logger.info(f"Skipping invalid book title: '{book_title}'")
                    continue
                
                logger.info(f"Verifying book exists: '{book_title}' by '{book_author}'")
                
                # Verify the book exists in Open Library before creating
                book_info = verify_book_exists(book_title, book_author)
                
                if not book_info["exists"]:
                    logger.info(f"Book not found in Open Library, skipping: '{book_title}'")
                    continue
                
                # Use canonical title/author from Open Library if available
                verified_title = book_info.get("title") or book_title
                verified_author = book_info.get("author") or book_author
                
                logger.info(f"Book verified: '{verified_title}' by '{verified_author}'")
                
                # Create or get book (avoid duplicates)
                book, created = Book.objects.get_or_create(
                    episode=episode,
                    title=verified_title,
                    defaults={
                        "author": verified_author,
                        "description": book_data.get("description", "").strip(),
                    },
                )

                # Update author and description if book already existed
                if not created:
                    updated = False
                    if verified_author and not book.author:
                        book.author = verified_author
                        updated = True
                    if book_data.get("description") and not book.description:
                        book.description = book_data.get("description", "").strip()
                        updated = True
                    if updated:
                        book.save()

                # Fetch and download cover image if not already set
                if created and not book.cover_image:
                    # Use cover_id from verification if available
                    if book_info.get("cover_id"):
                        cover_url = f"https://covers.openlibrary.org/b/id/{book_info['cover_id']}-L.jpg"
                    else:
                        cover_url = fetch_book_cover(book.title, book.author)
                    if cover_url:
                        download_and_save_cover(book, cover_url)

                # Generate purchase link if not already set
                if created and not book.purchase_link:
                    from .utils import generate_bookshop_affiliate_url

                    purchase_url = generate_bookshop_affiliate_url(
                        book.title, book.author
                    )
                    if purchase_url:
                        book.purchase_link = purchase_url
                        book.save(update_fields=["purchase_link"])

        # Mark raw_data as processed
        if hasattr(episode, "raw_data") and episode.raw_data:
            from django.utils import timezone

            episode.raw_data.processed = True
            episode.raw_data.processed_at = timezone.now()
            episode.raw_data.save(update_fields=["processed", "processed_at"])
            logger.info(f"Marked raw_data as processed for episode {episode_id}")

        return result

    except Episode.DoesNotExist:
        logger.warning(f"Episode {episode_id} does not exist")
        return {"has_book": False, "books": [], "reasoning": "Episode not found"}
    except Exception as e:
        logger.exception(f"Error extracting books from episode {episode_id}: {e}")
        return {"has_book": False, "books": [], "reasoning": f"Error: {str(e)}"}
