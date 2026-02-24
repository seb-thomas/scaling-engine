"""
Backfill historical episodes for a brand.

Usage:
    python manage.py backfill_episodes --brand 2 --max-episodes 100 --since 2024-01-01
    python manage.py backfill_episodes --brand 2 --max-episodes 50 --extract
"""
from django.core.management.base import BaseCommand
from stations.models import Brand, Episode
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.bbc_episode_spider import BbcEpisodeSpider


class Command(BaseCommand):
    help = "Backfill historical episodes for a brand (scrape older episodes)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--brand",
            type=int,
            required=True,
            help="Brand ID to backfill",
        )
        parser.add_argument(
            "--max-episodes",
            type=int,
            default=100,
            help="Maximum number of new episodes to scrape (default: 100)",
        )
        parser.add_argument(
            "--since",
            type=str,
            default=None,
            help="Date floor in YYYY-MM-DD format (e.g. 2024-01-01)",
        )
        parser.add_argument(
            "--extract",
            action="store_true",
            help="Run AI extraction on newly scraped episodes",
        )

    def handle(self, *args, **options):
        brand_id = options["brand"]
        max_episodes = options["max_episodes"]
        since = options["since"]
        extract = options["extract"]

        try:
            brand = Brand.objects.get(pk=brand_id)
        except Brand.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Brand {brand_id} not found"))
            return

        before_count = Episode.objects.filter(brand=brand).count()

        self.stdout.write(f"Backfilling {brand.name} (ID: {brand_id})")
        self.stdout.write(f"  Max episodes: {max_episodes}")
        self.stdout.write(f"  Since: {since or 'no limit'}")
        self.stdout.write(f"  Current episodes: {before_count}")
        self.stdout.write("")

        settings = get_project_settings()
        settings["LOG_LEVEL"] = "INFO"

        process = CrawlerProcess(settings)
        spider_kwargs = {"brand_id": brand_id, "max_episodes": max_episodes}
        if since:
            spider_kwargs["since"] = since

        process.crawl(BbcEpisodeSpider, **spider_kwargs)
        process.start()

        after_count = Episode.objects.filter(brand=brand).count()
        new_episodes = after_count - before_count

        self.stdout.write(
            self.style.SUCCESS(
                f"\nBackfill complete: {new_episodes} new episodes "
                f"({before_count} -> {after_count})"
            )
        )

        if extract and new_episodes > 0:
            from stations.tasks import ai_extract_books_task

            scraped = Episode.objects.filter(
                brand=brand, status=Episode.STATUS_SCRAPED
            )
            queued = 0
            for episode in scraped:
                episode.status = Episode.STATUS_QUEUED
                episode.last_error = None
                episode.save(update_fields=["status", "last_error"])
                ai_extract_books_task.delay(episode.id)
                queued += 1
            self.stdout.write(f"Queued AI extraction for {queued} episodes")
