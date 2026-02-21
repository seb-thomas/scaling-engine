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
    clean_date = (
        date_text.split(",")[-1].strip() if "," in date_text else date_text.strip()
    )
    clean_date = clean_date.split("·")[0].strip() if "·" in clean_date else clean_date

    # Try common BBC date formats
    date_formats = [
        "%d %b %Y",  # "24 Nov 2025"
        "%d %B %Y",  # "24 November 2025"
        "%Y-%m-%d",  # "2025-11-24"
        "%d/%m/%Y",  # "24/11/2025"
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
- Every extracted book MUST have an identified author. If the text does not name the author, do not extract the book. Never use "Unknown", "N/A", "Various" etc. as author — either provide the real name or skip the book.
- Require author + book title, OR explicit book-type words: "book", "novel", "short story collection", "autobiography", "memoir".
- "Thriller" or "comedy" alone = often TV/film, not books. We describe books as "thrilling" or "hilarious". Do not extract titles that could be film/TV unless there is author + book signal (e.g. "the contemporary thriller Lurker" = TV show, NOT a book).
- Exclude when context is adaptation, play, or musical. Signals: adaptation, adapted, film, movie, director, theatre, stage, screen, play, musical, transformed into, starring, choreographer, BBC adaptation, RSC production, West End. "Play" = theatre, not a book. "Musical based on [book]" = segment is about the musical, not the book.
- Each book description must match the book title; do not mix descriptions between books.

INCLUDE examples: "Mark Haddon's autobiography Leaving Home"; "Eric Schlosser's book Fast Food Nation... talks to the author"; "George Saunders' new book, Vigil"; prize announcements with author + book; "short story collection by Joy Williams"; "have read James Meek's book Your Life Without Me".

EXCLUDE examples: "Anne Brontë biographer" (no book); "thriller Lurker" (TV show); "BBC adaptation of Lord of the Flies"; "A Christmas Carol... transformed into hip hop dance"; "her new play My Brother's a Genius"; "RSC's new production of Cyrano de Bergerac"; "musical based on Rachel's hit book The Unlikely Pilgrimage of Harold Fry" (context is the musical).

Return JSON only:
{{
    "has_book": true/false,
    "confidence": 0.95,
    "books": [
        {{
            "title": "Book Title",
            "author": "Author Name",
            "description": "A brief, engaging description of what the book is about"
        }}
    ],
    "reasoning": "Brief explanation of your decision"
}}

confidence is your overall confidence in the decision (0.0-1.0). 0.9+ = clear-cut, 0.7-0.9 = probable, <0.7 = uncertain. Return ONLY valid JSON, no additional text."""

        for attempt in range(max_retries + 1):
            try:
                message = self.client.messages.create(
                    model="claude-sonnet-4-6",  # Reliable instruction-following
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from response
                response_text = message.content[0].text.strip()

                # Strip markdown code fences if present
                if response_text.startswith("```"):
                    response_text = response_text.split("\n", 1)[1]
                    response_text = response_text.rsplit("```", 1)[0].strip()

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
                headers={"User-Agent": "Mozilla/5.0 (compatible; RadioReads/1.0)"},
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


def _set_episode_failed(episode, error: Exception) -> None:
    """Set episode status to FAILED and store short error message."""
    from .models import Episode

    short = (str(error)[:200]) if str(error) else "Extraction error"
    episode.status = Episode.STATUS_FAILED
    episode.last_error = short
    episode.save(update_fields=["status", "last_error"])


def extract_books_from_episode(episode_id: int) -> Dict:
    """
    Extract book information from an episode using AI.

    Reads from episode.scraped_data, writes extraction_result and status to Episode.
    Replaces all books for the episode (delete then create). Sets PROCESSED or FAILED.
    """
    from django.utils import timezone

    from .models import Book, Episode

    try:
        episode = Episode.objects.get(pk=episode_id)
    except Episode.DoesNotExist:
        logger.warning(f"Episode {episode_id} does not exist")
        return {"has_book": False, "books": [], "reasoning": "Episode not found"}

    extractor = get_book_extractor()
    if not extractor.is_available():
        episode.status = Episode.STATUS_FAILED
        episode.last_error = "API not configured"
        episode.save(update_fields=["status", "last_error"])
        return {"has_book": False, "books": [], "reasoning": "API not configured"}

    # Text from scraped_data or fallback to title
    text_to_analyze = episode.title
    if episode.scraped_data:
        raw_title = episode.scraped_data.get("title", episode.title)
        raw_description = episode.scraped_data.get("description", "")
        text_to_analyze = f"{raw_title}. {raw_description}".strip()

    try:
        result = extractor.extract_books(text_to_analyze)
    except Exception as e:
        _set_episode_failed(episode, e)
        raise

    try:
        # Persist extraction result and overall confidence
        episode.extraction_result = {
            "has_book": result.get("has_book", False),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning", ""),
            "books": result.get("books", []),
        }
        episode.ai_confidence = result.get("confidence")

        # Replace books: delete all for this episode, then create from result
        Book.objects.filter(episode=episode).delete()

        from .utils import (
            generate_bookshop_affiliate_url,
            verify_book_exists,
        )

        new_books = []
        for book_data in result.get("books", []):
            book_title = book_data.get("title", "").strip()
            book_author = book_data.get("author", "").strip()
            if not book_title or book_title.upper() in [
                "N/A", "NA", "UNKNOWN", "TBD", "TBA",
            ]:
                continue
            # Skip books without a real author
            if not book_author or book_author.upper() in [
                "N/A", "NA", "UNKNOWN", "TBD", "TBA", "VARIOUS",
            ]:
                logger.info(
                    f"Skipping '{book_title}': no author identified"
                )
                continue

            # Verify via Google Books — skip if not found (likely not a real book)
            book_info = verify_book_exists(book_title, book_author)
            if not book_info["exists"]:
                logger.info(
                    f"Skipping '{book_title}' by {book_author}: "
                    f"not found on Google Books"
                )
                continue

            use_title = book_info.get("title") or book_title
            use_author = book_info.get("author") or book_author

            book = Book.objects.create(
                episode=episode,
                title=use_title,
                author=use_author,
                description=book_data.get("description", "").strip(),
                google_books_verified=True,
            )
            new_books.append(book)
            cover_url = book_info.get("cover_url") or ""
            if cover_url:
                download_and_save_cover(book, cover_url)
            purchase_url = generate_bookshop_affiliate_url(book.title, book.author)
            if purchase_url:
                book.purchase_link = purchase_url
                book.save(update_fields=["purchase_link"])

        episode.has_book = len(new_books) > 0
        if not episode.aired_at and episode.scraped_data:
            date_text = episode.scraped_data.get("date_text")
            if date_text:
                parsed = _parse_date(date_text)
                if parsed:
                    episode.aired_at = parsed

        episode.status = Episode.STATUS_PROCESSED
        episode.processed_at = timezone.now()
        episode.last_error = None
        episode.save(
            update_fields=[
                "extraction_result", "ai_confidence", "has_book",
                "aired_at", "status", "processed_at", "last_error",
            ]
        )
        return result
    except Exception as e:
        _set_episode_failed(episode, e)
        raise
