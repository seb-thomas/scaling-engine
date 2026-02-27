"""
Generic RSS feed scraper for podcast-based shows.

Works for any brand with spider_name="rss" — just set brand.url to the feed URL.
"""

import logging
from datetime import datetime

import feedparser

from .models import Episode

logger = logging.getLogger(__name__)


def scrape_rss_brand(brand, max_episodes=50, since_date=None):
    """
    Scrape episodes from an RSS feed for a brand.

    Args:
        brand: Brand instance with url pointing to an RSS feed
        max_episodes: Maximum number of new episodes to create
        since_date: Optional ISO date string (YYYY-MM-DD) — skip entries older than this

    Returns:
        dict with new_episodes count
    """
    feed = feedparser.parse(brand.url)
    if feed.bozo and not feed.entries:
        logger.error(f"Failed to parse RSS feed for {brand.name}: {feed.bozo_exception}")
        return {"new_episodes": 0}

    since_dt = None
    if since_date:
        since_dt = datetime.fromisoformat(since_date)

    created = 0
    for entry in feed.entries:
        if created >= max_episodes:
            break

        url = entry.get("link", "")
        if not url:
            continue

        if Episode.objects.filter(url=url).exists():
            continue

        # Parse published date for since_date filtering
        date_text = entry.get("published", "")
        if since_dt and date_text:
            from email.utils import parsedate_to_datetime
            try:
                entry_dt = parsedate_to_datetime(date_text)
                if entry_dt.replace(tzinfo=None) < since_dt:
                    continue
            except (ValueError, TypeError):
                pass

        title = entry.get("title", "")
        description = entry.get("summary", "")

        Episode.objects.create(
            brand=brand,
            title=title[:255],
            url=url,
            scraped_data={
                "title": title,
                "url": url,
                "description": description,
                "date_text": date_text,
            },
            status=Episode.STATUS_SCRAPED,
        )
        created += 1

    logger.info(f"RSS scrape for {brand.name}: {created} new episodes")
    return {"new_episodes": created}
