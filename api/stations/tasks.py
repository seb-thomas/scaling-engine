from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from django.db import DatabaseError
from datetime import datetime
from .utils import contains_keywords
from .ai_utils import extract_books_from_episode, get_book_extractor
from .models import Brand, Episode, RawEpisodeData

logger = get_task_logger(__name__)


@shared_task(
    name="stations.tasks.contains_keywords_task",
    bind=True,
    autoretry_for=(DatabaseError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    max_retries=3,
)
def contains_keywords_task(self, episode_id):
    """Legacy keyword-based book detection task."""
    logger.info(f"Processing keywords for episode {episode_id}")
    try:
        return contains_keywords(episode_id)
    except Exception as e:
        logger.error(f"Error processing episode {episode_id}: {e}")
        raise


@shared_task(
    name="stations.tasks.ai_extract_books_task",
    bind=True,
    autoretry_for=(DatabaseError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def ai_extract_books_task(self, episode_id):
    """
    AI-powered book extraction task using Claude.

    This task uses Claude AI to intelligently extract book mentions
    from episode titles, replacing simple keyword matching with
    context-aware natural language understanding.
    """
    logger.info(f"AI extracting books for episode {episode_id}")
    try:
        result = extract_books_from_episode(episode_id)
        logger.info(
            f"AI extraction complete for episode {episode_id}: "
            f"has_book={result['has_book']}, books={len(result.get('books', []))}"
        )
        return result
    except Exception as e:
        logger.error(f"Error in AI extraction for episode {episode_id}: {e}")
        raise


@shared_task(name="stations.tasks.scrape_all_brands")
def scrape_all_brands(max_episodes_per_brand=50):
    """
    Scrape episodes from all active brands (radio shows).

    This task runs the BBC episode spider for each brand in the database,
    discovering new episodes and triggering AI extraction for book mentions.
    """
    logger.info("Starting scrape for all brands")

    brands = Brand.objects.all()
    if not brands.exists():
        logger.warning("No brands found in database. Please add brands first.")
        return {"status": "no_brands", "scraped": 0}

    # Import Scrapy modules
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from scraper.spiders.bbc_episode_spider import BbcEpisodeSpider

    # Create a single crawler process for all brands
    # (CrawlerProcess can only be started once)
    settings = get_project_settings()
    settings["LOG_LEVEL"] = "INFO"

    process = CrawlerProcess(settings)

    # Queue all brands to be crawled
    for brand in brands:
        logger.info(f"Queueing brand for scraping: {brand.name} (ID: {brand.id})")
        process.crawl(
            BbcEpisodeSpider, brand_id=brand.id, max_episodes=max_episodes_per_brand
        )

    # Start crawling all brands
    try:
        process.start()  # This blocks until all spiders finish
        logger.info("All brands scraped successfully")
        return {"status": "complete", "brands_queued": brands.count()}
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="stations.tasks.extract_books_from_new_episodes")
def extract_books_from_new_episodes():
    """
    Run AI extraction on episodes that haven't been processed yet.

    This finds episodes without book extraction results and processes them
    with Claude AI to detect book mentions.
    """
    logger.info("Starting AI extraction for new episodes")

    # Find episodes that haven't been processed (no related books)
    episodes = Episode.objects.filter(book__isnull=True)[
        :50
    ]  # Process in batches of 50

    if not episodes.exists():
        logger.info("No new episodes to process")
        return {"status": "no_new_episodes", "processed": 0}

    processed = 0
    books_found = 0

    for episode in episodes:
        logger.info(f"Processing episode: {episode.title} (ID: {episode.id})")
        try:
            # Trigger AI extraction task
            result = ai_extract_books_task.delay(episode.id)
            processed += 1

            # Note: We can't check the result here since it's async
            # The task will handle saving books to the database

        except Exception as e:
            logger.error(f"Error triggering extraction for episode {episode.id}: {e}")

    logger.info(f"Triggered AI extraction for {processed} episodes")
    return {"status": "complete", "episodes_processed": processed}


