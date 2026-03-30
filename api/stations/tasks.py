from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from django.db import DatabaseError
from django.utils import timezone
from datetime import datetime
from .utils import contains_keywords
from .ai_utils import extract_books_from_episode, get_book_extractor
from .models import Brand, Episode, Book

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

        # Skip if already past extraction — prevents wasting API calls on duplicates
        terminal_stages = (
            Episode.STAGE_EXTRACTION_NO_BOOKS, Episode.STAGE_EXTRACTION_FAILED,
            Episode.STAGE_VERIFICATION_QUEUED, Episode.STAGE_VERIFICATION_FAILED,
            Episode.STAGE_REVIEW, Episode.STAGE_COMPLETE,
        )
        if episode.stage in terminal_stages:
            logger.info(
                f"Episode {episode_id} already {episode.stage}, skipping"
            )
            return {"skipped": True, "reason": f"already {episode.stage}"}

        episode.stage = Episode.STAGE_EXTRACTING
        episode.task_id = self.request.id
        episode.last_error = None
        episode.status_changed_at = timezone.now()
        episode.save(update_fields=["stage", "task_id", "last_error", "status_changed_at"])

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

    if brand.spider_name == "wnyc_api":
        from .wnyc_utils import scrape_wnyc_brand
        result = scrape_wnyc_brand(brand, max_episodes=max_episodes)
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
        scrape_rss_brand(brand, max_episodes=max_episodes, since_date=since_date)
    elif brand.spider_name == "wnyc_api":
        from .wnyc_utils import scrape_wnyc_brand
        scrape_wnyc_brand(brand, max_episodes=max_episodes, since_date=since_date)
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

    # Unstick orphaned episodes (EXTRACTION_QUEUED/EXTRACTING for >60min)
    stuck = Episode.stuck(threshold_minutes=60)
    stuck_count = stuck.count()
    if stuck_count > 0:
        stuck.update(
            stage=Episode.STAGE_SCRAPED,
            last_error=None,
            task_id=None,
            status_changed_at=timezone.now(),
        )
        logger.warning(f"Reset {stuck_count} stuck episode(s) back to SCRAPED")

    # Find episodes with stage=SCRAPED (not yet processed)
    episodes = Episode.objects.filter(stage=Episode.STAGE_SCRAPED)[:50]

    if not episodes.exists():
        logger.info("No new episodes to process")
        return {"status": "no_new_episodes", "processed": 0}

    processed = 0

    for episode in episodes:
        logger.info(f"Queuing episode: {episode.title} (ID: {episode.id})")
        try:
            episode.stage = Episode.STAGE_EXTRACTION_QUEUED
            episode.last_error = None
            episode.status_changed_at = timezone.now()
            episode.save(update_fields=["stage", "last_error", "status_changed_at"])
            ai_extract_books_task.delay(episode.id)
            processed += 1
        except Exception as e:
            logger.error(f"Error triggering extraction for episode {episode.id}: {e}")

    logger.info(f"Triggered AI extraction for {processed} episodes")
    return {"status": "complete", "episodes_processed": processed}


@shared_task(name="stations.tasks.verify_pending_books")
def verify_pending_books(batch_size=20):
    """
    Verify pending books against Google Books API.

    Runs hourly. For each pending book:
    - Found → update canonical title/author, download cover, set verified
    - Not found → set not_found + timestamp
    - Rate limited → stop immediately
    Also cleans up not_found books older than 7 days.
    """
    from datetime import timedelta
    from django.db.models import Q
    from .utils import verify_book_exists, GoogleBooksRateLimited, generate_bookshop_affiliate_url
    from .ai_utils import download_and_save_cover

    pending = Book.objects.filter(
        verification_status=Book.VERIFICATION_PENDING
    )[:batch_size]

    verified_count = 0
    not_found_count = 0

    for book in pending:
        try:
            book_info = verify_book_exists(book.title, book.author)
        except GoogleBooksRateLimited:
            logger.warning("Google Books rate limited during verification, stopping batch")
            break

        if book_info["exists"]:
            canonical_title = book_info.get("title") or book.title
            canonical_author = book_info.get("author") or book.author

            # Sanity check: Google Books result must resemble what we searched for.
            # Study guides ("Summary of X") and wrong editions often outrank originals.
            ai_title_lower = book.title.lower()
            gb_title_lower = canonical_title.lower()
            ai_author_lower = book.author.lower()
            gb_author_lower = canonical_author.lower()
            title_ok = (
                ai_title_lower in gb_title_lower
                or gb_title_lower in ai_title_lower
            )
            author_ok = (
                not ai_author_lower
                or ai_author_lower.split()[-1] in gb_author_lower
            )
            if not (title_ok and author_ok):
                logger.warning(
                    f"Google Books mismatch for '{book.title}' by {book.author}: "
                    f"got '{canonical_title}' by {canonical_author} — marking not_found"
                )
                book.verification_status = Book.VERIFICATION_NOT_FOUND
                book.verification_checked_at = timezone.now()
                book.save(update_fields=["verification_status", "verification_checked_at"])
                not_found_count += 1
                continue

            # Check if a verified book with the canonical title/author already exists
            existing = Book.objects.filter(
                title__iexact=canonical_title,
                author__iexact=canonical_author,
                verification_status=Book.VERIFICATION_VERIFIED,
            ).exclude(pk=book.pk).first()

            if existing:
                # Merge: move episodes to existing book, delete this one
                for episode in book.episodes.all():
                    existing.episodes.add(episode)
                logger.info(
                    f"Merged duplicate '{book.title}' into verified '{existing.title}'"
                )
                book.delete()
                verified_count += 1
                continue

            # Keep AI-extracted title/author — Google Books often returns
            # subtitles, edition names, or study guides that are less clean.
            book.verification_status = Book.VERIFICATION_VERIFIED
            book.verification_checked_at = timezone.now()
            book.save(update_fields=[
                "verification_status", "verification_checked_at",
            ])

            # Download cover
            cover_url = book_info.get("cover_url") or ""
            if cover_url:
                download_and_save_cover(book, cover_url)
            else:
                book.cover_fetch_error = "No cover available on Google Books"
                book.save(update_fields=["cover_fetch_error"])

            # Update purchase link with canonical info
            purchase_url = generate_bookshop_affiliate_url(book.title, book.author)
            if purchase_url:
                book.purchase_link = purchase_url
                book.save(update_fields=["purchase_link"])

            # Update stage on linked episodes
            for episode in book.episodes.all():
                new_stage = episode.compute_stage_after_verification()
                if new_stage != episode.stage:
                    episode.stage = new_stage
                    episode.save(update_fields=["stage"])

            verified_count += 1
            logger.info(f"Verified: '{book.title}' by {book.author}")

        elif not book_info.get("error"):
            # Genuinely not found (not an API error)
            book.verification_status = Book.VERIFICATION_NOT_FOUND
            book.verification_checked_at = timezone.now()
            book.save(update_fields=["verification_status", "verification_checked_at"])
            not_found_count += 1
            logger.info(f"Not found on Google Books: '{book.title}' by {book.author}")

            # Update stage on linked episodes
            for episode in book.episodes.all():
                new_stage = episode.compute_stage_after_verification()
                if new_stage != episode.stage:
                    episode.stage = new_stage
                    episode.save(update_fields=["stage"])
        else:
            # API error (timeout etc.) — skip, will retry next hour
            logger.warning(
                f"Skipping '{book.title}': API error {book_info['error']}"
            )

    # Cleanup: delete not_found books older than 7 days
    cutoff = timezone.now() - timedelta(days=7)
    stale_books = Book.objects.filter(
        verification_status=Book.VERIFICATION_NOT_FOUND,
        verification_checked_at__lt=cutoff,
    )
    deleted_count = 0
    for book in stale_books:
        # Capture linked episodes before deleting
        episodes = list(book.episodes.all())
        book_title = book.title
        book.delete()
        deleted_count += 1
        logger.info(f"Deleted stale not_found book: '{book_title}'")

    logger.info(
        f"Verification complete: {verified_count} verified, "
        f"{not_found_count} not found, {deleted_count} stale deleted"
    )
    return {
        "verified": verified_count,
        "not_found": not_found_count,
        "stale_deleted": deleted_count,
    }
