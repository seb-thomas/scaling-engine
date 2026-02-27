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
    max_retries=0,
)
def ai_extract_books_task(self, episode_id):
    """
    AI-powered book extraction task using Claude.

    No auto-retry — failed episodes are caught by the 30-minute
    extraction task which unsticks and re-queues them. This prevents
    retry pile-ups during deploys when DB connections drop transiently.
    """
    logger.info(f"AI extracting books for episode {episode_id}")
    try:
        episode = Episode.objects.get(pk=episode_id)

        # Skip if already processed — prevents wasting API calls on duplicates
        if episode.status in (Episode.STATUS_PROCESSED, Episode.STATUS_FAILED):
            logger.info(
                f"Episode {episode_id} already {episode.status}, skipping"
            )
            return {"skipped": True, "reason": f"already {episode.status}"}

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


@shared_task(name="stations.tasks.scrape_brand")
def scrape_brand(brand_id, max_episodes=50):
    """Scrape recent episodes for a single brand."""
    brand = Brand.objects.get(pk=brand_id)
    logger.info(f"Scraping {brand.name} (max {max_episodes} episodes)")

    if brand.spider_name == "rss":
        from .rss_utils import scrape_rss_brand
        result = scrape_rss_brand(brand, max_episodes=max_episodes)
        return {"status": "complete", "brand": brand.name, "new_episodes": result["new_episodes"]}

    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from scraper.spiders.bbc_episode_spider import BbcEpisodeSpider

    before_count = Episode.objects.filter(brand=brand).count()

    settings = get_project_settings()
    settings["LOG_LEVEL"] = "INFO"
    process = CrawlerProcess(settings)
    process.crawl(BbcEpisodeSpider, brand_id=brand_id, max_episodes=max_episodes)

    try:
        process.start()
    except Exception as e:
        logger.error(f"Error scraping {brand.name}: {e}")
        return {"status": "error", "error": str(e)}

    after_count = Episode.objects.filter(brand=brand).count()
    new = after_count - before_count
    logger.info(f"Scraped {brand.name}: {new} new episodes")
    return {"status": "complete", "brand": brand.name, "new_episodes": new}


@shared_task(name="stations.tasks.scrape_all_brands")
def scrape_all_brands(max_episodes_per_brand=50, stagger_seconds=600):
    """
    Dispatch per-brand scrape tasks staggered over time.

    Each brand gets its own scrape_brand task, offset by stagger_seconds
    so that many brands don't all hit BBC Sounds simultaneously.
    """
    brands = list(Brand.objects.all())
    if not brands:
        logger.warning("No brands found in database. Please add brands first.")
        return {"status": "no_brands", "scraped": 0}

    logger.info(
        f"Dispatching staggered scrape for {len(brands)} brands "
        f"({stagger_seconds}s apart, max {max_episodes_per_brand} eps each)"
    )

    for i, brand in enumerate(brands):
        delay = i * stagger_seconds
        scrape_brand.apply_async(
            kwargs={"brand_id": brand.id, "max_episodes": max_episodes_per_brand},
            countdown=delay,
        )
        logger.info(f"Queued scrape for {brand.name} (delay={delay}s)")

    return {"status": "dispatched", "brands": len(brands)}


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

    if brand.spider_name == "rss":
        from .rss_utils import scrape_rss_brand
        result = scrape_rss_brand(brand, max_episodes=max_episodes, since_date=since_date)
        new_episodes = result["new_episodes"]
    else:
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

    # Note: extraction is triggered automatically by the Episode post_save signal
    # when extract=True, we just log that extraction will happen via the signal.
    # No need to explicitly queue tasks here — the signal fires on episode creation.
    if extract and new_episodes > 0:
        logger.info(
            f"AI extraction will run for {new_episodes} episodes via post_save signal"
        )

    return {
        "status": "complete",
        "brand": brand.name,
        "new_episodes": new_episodes,
        "total_episodes": after_count,
    }


@shared_task(name="stations.tasks.backfill_all_brands")
def backfill_all_brands(max_episodes_per_brand=25, stagger_seconds=600):
    """
    Incremental backfill: dispatch per-brand backfill tasks staggered over time.

    Each brand gets its own backfill_brand_task, offset by stagger_seconds
    so that 10 brands don't all hit BBC Sounds simultaneously.
    Extraction is triggered automatically by post_save signal.
    """
    brands = list(Brand.objects.all())
    if not brands:
        logger.warning("No brands found")
        return {"status": "no_brands"}

    logger.info(
        f"Dispatching staggered backfill for {len(brands)} brands "
        f"({stagger_seconds}s apart, max {max_episodes_per_brand} eps each)"
    )

    for i, brand in enumerate(brands):
        delay = i * stagger_seconds
        backfill_brand_task.apply_async(
            kwargs={
                "brand_id": brand.id,
                "max_episodes": max_episodes_per_brand,
                "extract": False,  # signal handles extraction on create
            },
            countdown=delay,
        )
        logger.info(f"Queued backfill for {brand.name} (delay={delay}s)")

    return {"status": "dispatched", "brands": len(brands)}


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
