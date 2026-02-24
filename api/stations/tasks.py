from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from django.db import DatabaseError
from django.utils import timezone
from datetime import datetime
from .utils import contains_keywords
from .ai_utils import extract_books_from_episode, get_book_extractor
from .models import Brand, Episode

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
        episode = Episode.objects.get(pk=episode_id)
        episode.status = Episode.STATUS_PROCESSING
        episode.task_id = self.request.id
        episode.last_error = None
        episode.status_changed_at = timezone.now()
        episode.save(update_fields=["status", "task_id", "last_error", "status_changed_at"])

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


@shared_task(name="stations.tasks.backfill_brand_task")
def backfill_brand_task(brand_id, max_episodes=100, since_date=None, extract=False):
    """
    Backfill historical episodes for a brand.

    Runs the spider with a higher max_episodes and optional date floor.
    Optionally triggers AI extraction on newly scraped episodes.
    """
    logger.info(
        f"Starting backfill for brand {brand_id}: "
        f"max_episodes={max_episodes}, since={since_date}, extract={extract}"
    )

    brand = Brand.objects.get(pk=brand_id)

    # Count episodes before scraping
    before_count = Episode.objects.filter(brand=brand).count()

    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from scraper.spiders.bbc_episode_spider import BbcEpisodeSpider

    settings = get_project_settings()
    settings["LOG_LEVEL"] = "INFO"

    process = CrawlerProcess(settings)
    spider_kwargs = {"brand_id": brand_id, "max_episodes": max_episodes}
    if since_date:
        spider_kwargs["since"] = since_date

    process.crawl(BbcEpisodeSpider, **spider_kwargs)

    try:
        process.start()
    except Exception as e:
        logger.error(f"Error during backfill scrape: {e}")
        return {"status": "error", "error": str(e)}

    after_count = Episode.objects.filter(brand=brand).count()
    new_episodes = after_count - before_count

    logger.info(f"Backfill complete for {brand.name}: {new_episodes} new episodes")

    # Optionally trigger extraction on newly scraped episodes
    if extract and new_episodes > 0:
        scraped = Episode.objects.filter(brand=brand, status=Episode.STATUS_SCRAPED)
        queued = 0
        for episode in scraped:
            episode.status = Episode.STATUS_QUEUED
            episode.last_error = None
            episode.status_changed_at = timezone.now()
            episode.save(update_fields=["status", "last_error", "status_changed_at"])
            ai_extract_books_task.delay(episode.id)
            queued += 1
        logger.info(f"Queued AI extraction for {queued} episodes")

    return {
        "status": "complete",
        "brand": brand.name,
        "new_episodes": new_episodes,
        "total_episodes": after_count,
    }


@shared_task(name="stations.tasks.extract_books_from_new_episodes")
def extract_books_from_new_episodes():
    """
    Run AI extraction on episodes that haven't been processed yet.

    This finds episodes without book extraction results and processes them
    with Claude AI to detect book mentions.
    """
    logger.info("Starting AI extraction for new episodes")

    # Unstick orphaned episodes (QUEUED/PROCESSING for >60min)
    stuck = Episode.stuck(threshold_minutes=60)
    stuck_count = stuck.count()
    if stuck_count > 0:
        stuck.update(
            status=Episode.STATUS_SCRAPED,
            last_error=None,
            task_id=None,
            status_changed_at=timezone.now(),
        )
        logger.warning(f"Reset {stuck_count} stuck episode(s) back to SCRAPED")

    # Find episodes with status=SCRAPED (not yet processed)
    episodes = Episode.objects.filter(status=Episode.STATUS_SCRAPED)[:50]

    if not episodes.exists():
        logger.info("No new episodes to process")
        return {"status": "no_new_episodes", "processed": 0}

    processed = 0

    for episode in episodes:
        logger.info(f"Queuing episode: {episode.title} (ID: {episode.id})")
        try:
            episode.status = Episode.STATUS_QUEUED
            episode.last_error = None
            episode.status_changed_at = timezone.now()
            episode.save(update_fields=["status", "last_error", "status_changed_at"])
            ai_extract_books_task.delay(episode.id)
            processed += 1
        except Exception as e:
            logger.error(f"Error triggering extraction for episode {episode.id}: {e}")

    logger.info(f"Triggered AI extraction for {processed} episodes")
    return {"status": "complete", "episodes_processed": processed}
