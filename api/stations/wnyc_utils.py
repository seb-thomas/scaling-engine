"""
WNYC API scraper for shows hosted on wnyc.org.

Works for any brand with spider_name="wnyc_api" — set brand.url to the WNYC show page
(e.g. https://www.wnyc.org/shows/splendid-table).

Uses the public WNYC JSON API: no auth, no Scrapy, no headless browser.
"""

import json
import logging
import time
import urllib.error
import urllib.request
from datetime import datetime

from .models import Episode

logger = logging.getLogger(__name__)

API_BASE = "https://api.wnyc.org/api/v3/story/"
USER_AGENT = "RadioReads/1.0 (https://radioreads.fun)"
PAGE_SIZE = 10
REQUEST_DELAY = 1  # seconds between paginated requests


def _get_show_slug(brand):
    """Extract show slug from brand URL (last path segment)."""
    url = brand.url.rstrip("/")
    return url.split("/")[-1]


def _fetch_page(show_slug, page):
    """Fetch a single page from the WNYC API. Returns parsed JSON or None."""
    url = (
        f"{API_BASE}?show={show_slug}"
        f"&limit={PAGE_SIZE}&ordering=-newsdate&page={page}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            logger.warning(
                f"WNYC API returned {e.code} on page {page} for {show_slug} — stopping"
            )
            return None
        raise
    except urllib.error.URLError as e:
        logger.error(f"WNYC API request failed for {show_slug} page {page}: {e}")
        return None


def scrape_wnyc_brand(brand, max_episodes=50, since_date=None):
    """
    Scrape episodes from the WNYC API for a brand.

    Args:
        brand: Brand instance with url pointing to a WNYC show page
        max_episodes: Maximum number of new episodes to create
        since_date: Optional ISO date string (YYYY-MM-DD) — skip stories older than this

    Returns:
        dict with new_episodes count
    """
    show_slug = _get_show_slug(brand)
    logger.info(f"WNYC API scrape for {brand.name} (slug={show_slug})")

    since_dt = None
    if since_date:
        since_dt = datetime.fromisoformat(since_date)

    created = 0
    page = 1
    hit_date_floor = False

    while created < max_episodes and not hit_date_floor:
        if page > 1:
            time.sleep(REQUEST_DELAY)

        data = _fetch_page(show_slug, page)
        if not data:
            break

        stories = data.get("data", [])
        if not stories:
            break

        for story in stories:
            if created >= max_episodes:
                break

            attrs = story.get("attributes", {})
            story_url = attrs.get("url", "")
            if not story_url:
                continue

            # Normalize http → https
            if story_url.startswith("http://"):
                story_url = "https://" + story_url[7:]

            # Check date floor before dedup (stories are newest-first)
            newsdate = attrs.get("newsdate", "")
            if since_dt and newsdate:
                try:
                    story_dt = datetime.fromisoformat(newsdate)
                    if story_dt.replace(tzinfo=None) < since_dt:
                        hit_date_floor = True
                        break
                except (ValueError, TypeError):
                    pass

            if Episode.objects.filter(url=story_url).exists():
                continue
            # Also dedup by title — WNYC API can return both slug and GUID URLs
            # for the same story
            if title and Episode.objects.filter(brand=brand, title=title[:255]).exists():
                continue

            title = attrs.get("title", "")
            # Prefer body (full HTML), fall back to tease (short text)
            description = attrs.get("body", "") or attrs.get("tease", "")

            Episode.objects.create(
                brand=brand,
                title=title[:255],
                url=story_url,
                scraped_data={
                    "title": title,
                    "url": story_url,
                    "description": description,
                    "date_text": newsdate,
                },
                stage=Episode.STAGE_SCRAPED,
            )
            created += 1

        # Check if there are more pages
        total_pages = (
            data.get("meta", {}).get("pagination", {}).get("pages", 1)
        )
        if page >= total_pages:
            break
        page += 1

    logger.info(f"WNYC API scrape for {brand.name}: {created} new episodes")
    return {"new_episodes": created}
