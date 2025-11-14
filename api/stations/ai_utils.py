"""
AI-powered book extraction using Claude API.

This module uses Anthropic's Claude API to intelligently extract book mentions
from episode titles and descriptions, replacing simple keyword matching.
"""
import os
import logging
import json
from typing import Dict, List, Optional
from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)


class BookExtractor:
    """Extracts book information from text using Claude AI."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the book extractor.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("No Anthropic API key provided. AI extraction will be disabled.")
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
            return {'has_book': False, 'books': [], 'reasoning': 'API key not configured'}

        prompt = f"""Analyze this BBC radio episode title and determine if it mentions or discusses books, authors, or literature.

Episode title: "{text}"

Your task:
1. Determine if this episode is about books, authors, or literature
2. Extract any book titles and authors mentioned
3. Return JSON with the following structure:

{{
    "has_book": true/false,
    "books": [
        {{"title": "Book Title", "author": "Author Name", "confidence": 0.95}}
    ],
    "reasoning": "Brief explanation of your decision"
}}

Rules:
- Only return true if the episode is CLEARLY about books, authors, or literature
- Extract specific book titles when mentioned
- Confidence should be 0.0-1.0 (0.8+ for clear mentions, 0.5-0.8 for likely, <0.5 for uncertain)
- If no books are mentioned, return empty books array
- Be conservative: "bookshelf" or "bookstore" alone doesn't mean the episode is about a book

Return ONLY valid JSON, no additional text."""

        for attempt in range(max_retries + 1):
            try:
                message = self.client.messages.create(
                    model="claude-3-haiku-20240307",  # Fast and cost-effective
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract text from response
                response_text = message.content[0].text.strip()

                # Parse JSON response
                result = json.loads(response_text)

                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError("Response is not a dict")
                if 'has_book' not in result:
                    raise ValueError("Response missing 'has_book' field")

                # Ensure required fields
                result.setdefault('books', [])
                result.setdefault('reasoning', 'No reasoning provided')

                logger.info(f"AI extraction result: has_book={result['has_book']}, "
                           f"books_found={len(result['books'])}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.debug(f"Response was: {response_text[:200]}")
                if attempt < max_retries:
                    continue
                return {'has_book': False, 'books': [], 'reasoning': 'JSON parse error'}

            except (APIError, APITimeoutError, RateLimitError) as e:
                logger.error(f"Claude API error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    continue
                return {'has_book': False, 'books': [], 'reasoning': f'API error: {str(e)}'}

            except Exception as e:
                logger.exception(f"Unexpected error in AI extraction: {e}")
                return {'has_book': False, 'books': [], 'reasoning': f'Error: {str(e)}'}

        return {'has_book': False, 'books': [], 'reasoning': 'Max retries exceeded'}

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
            return {'has_book': False, 'books': [], 'reasoning': 'API not configured'}

        # Extract from title (could extend to description if available)
        result = extractor.extract_books(episode.title)

        # Update episode if books found
        if result['has_book'] and not episode.has_book:
            episode.has_book = True
            episode.save(update_fields=['has_book'])
            logger.info(f"Episode {episode_id} marked as has_book=True by AI")

        return result

    except Episode.DoesNotExist:
        logger.warning(f"Episode {episode_id} does not exist")
        return {'has_book': False, 'books': [], 'reasoning': 'Episode not found'}
    except Exception as e:
        logger.exception(f"Error extracting books from episode {episode_id}: {e}")
        return {'has_book': False, 'books': [], 'reasoning': f'Error: {str(e)}'}
