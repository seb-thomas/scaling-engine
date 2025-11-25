"""
AI-powered book extraction using Claude API.

This module uses Anthropic's Claude API to intelligently extract book mentions
from episode titles and descriptions, replacing simple keyword matching.
"""

import os
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError

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

        prompt = f"""Analyze this BBC radio episode text and determine if it mentions or discusses books, authors, or literature.

Episode text: "{text}"

Your task:
1. Determine if this episode is about books, authors, or literature
2. Extract any book titles and authors mentioned
3. Generate a brief, engaging description for each book (1-2 sentences about the book itself, NOT the episode)
4. Return JSON with the following structure:

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

Rules:
- Only return true if the episode is CLEARLY about books, authors, or literature
- Extract specific book titles when mentioned
- For each book, write a compelling 1-2 sentence description about what the book is about (not about the episode)
- If the episode text provides context about the book's content, use it to craft the description
- Confidence should be 0.0-1.0 (0.8+ for clear mentions, 0.5-0.8 for likely, <0.5 for uncertain)
- If no books are mentioned, return empty books array
- Be conservative: "bookshelf" or "bookstore" alone doesn't mean the episode is about a book

Return ONLY valid JSON, no additional text."""

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

        # Update episode and save books if found
        if result["has_book"]:
            if not episode.has_book:
                episode.has_book = True
                episode.save(update_fields=["has_book"])
                logger.info(f"Episode {episode_id} marked as has_book=True by AI")

            # Save extracted books to database
            from .models import Book
            from .utils import fetch_book_cover

            logger.info(
                f"Saving {len(result.get('books', []))} books to database for episode {episode_id}"
            )
            for book_data in result.get("books", []):
                book_title = book_data.get("title", "").strip()
                book_author = book_data.get("author", "").strip()
                logger.info(f"Processing book: {book_title}")
                if book_title:
                    # Create or get book (avoid duplicates)
                    book, created = Book.objects.get_or_create(
                        episode=episode,
                        title=book_title,
                        defaults={
                            "author": book_author,
                            "description": book_data.get("description", "").strip(),
                        },
                    )

                    # Update author and description if book already existed
                    if not created:
                        updated = False
                        if book_author and not book.author:
                            book.author = book_author
                            updated = True
                        if book_data.get("description") and not book.description:
                            book.description = book_data.get("description", "").strip()
                            updated = True
                        if updated:
                            book.save()

                    # Fetch cover image if not already set
                    if created and not book.cover_image:
                        cover_url = fetch_book_cover(book.title, book.author)
                        if cover_url:
                            book.cover_image = cover_url
                            book.save(update_fields=["cover_image"])
                            logger.info(f"Fetched cover image for {book_title}")

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
