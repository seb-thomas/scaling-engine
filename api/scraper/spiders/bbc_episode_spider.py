import re

import scrapy
from datetime import datetime
from scraper.items import EpisodeItem
from stations.models import Brand


class BbcEpisodeSpider(scrapy.Spider):
    name = "bbc_episodes"

    def __init__(self, brand_id=None, max_episodes=50, since=None, *args, **kwargs):
        super(BbcEpisodeSpider, self).__init__(*args, **kwargs)
        self.max_episodes = int(max_episodes) if max_episodes else 50
        self.episodes_scraped = 0
        self._raw_data_cache = {}  # Initialize cache for raw data
        self._hit_date_floor = False

        # Parse since date floor (e.g. "2024-01-01")
        if since:
            self.since_date = datetime.strptime(str(since), "%Y-%m-%d").date()
            self.logger.info(f"Date floor set: will stop at episodes before {self.since_date}")
        else:
            self.since_date = None

        if brand_id:
            self.brand = Brand.objects.get(pk=brand_id)
        else:
            # Try to find Front Row by name, otherwise get first brand
            self.brand = Brand.objects.filter(name__icontains="Front Row").first()
            if not self.brand:
                self.brand = Brand.objects.first()

    def start_requests(self):
        if not self.brand:
            self.logger.error(
                "No brand found. Please create a Brand first or pass brand_id parameter."
            )
            return

        self.logger.info(
            f"Scraping up to {self.max_episodes} episodes from: {self.brand.name}"
        )

        # BBC Sounds brand page directly lists episodes - no need to add /episodes/player
        episodes_url = self.brand.url.rstrip("/")

        self.logger.info(f"Starting scrape from: {episodes_url}")
        yield scrapy.Request(url=episodes_url, callback=self.parse)

    def parse(self, response):
        # Check if we've reached the limit
        if self.episodes_scraped >= self.max_episodes:
            self.logger.info(
                f"Reached maximum episodes limit ({self.max_episodes}). Stopping."
            )
            return

        episodes_found = 0

        # New BBC Sounds structure uses <li> elements with playable list cards
        for episode in response.css("li"):
            if self.episodes_scraped >= self.max_episodes:
                break

            # Look for links with aria-label containing episode info
            link = episode.css("a[aria-label*='release date']")
            if not link:
                continue

            item = EpisodeItem()

            # Extract title from aria-label or the visible title text
            aria_label = link.css("::attr(aria-label)").get()
            title_element = episode.css("span.sw-font-bold.sw-transition ::text").get()

            # Get URL from href
            url = link.css("::attr(href)").get()

            if not url:
                continue

            # Use the visible title if available, otherwise parse from aria-label
            if title_element:
                item["title"] = title_element.strip()
            elif aria_label:
                # Parse title from aria-label (format: "Title, release date: ..., duration: ...")
                title = aria_label.split(", release date:")[0].strip()
                item["title"] = title
            else:
                continue

            # Check date floor from aria-label (contains "release date: 24 Nov 2025")
            if self.since_date and aria_label and "release date:" in aria_label:
                try:
                    date_part = aria_label.split("release date:")[1].split(",")[0].strip()
                    episode_date = datetime.strptime(date_part, "%d %b %Y").date()
                    if episode_date < self.since_date:
                        self.logger.info(
                            f"Hit date floor: {item['title']} ({episode_date}) is before {self.since_date}. Stopping."
                        )
                        self._hit_date_floor = True
                        break
                except (ValueError, IndexError):
                    pass  # Can't parse date — continue scraping

            # Clean up the URL
            item["url"] = url.strip() if url else ""

            # Make URL absolute if it's relative
            if item["url"] and not item["url"].startswith("http"):
                item["url"] = response.urljoin(item["url"])

            # Extract date from the list page link text (e.g. "19 Feb 2026")
            date_text = link.css("::text").re_first(
                r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}"
            )

            # Skip if episode already exists in database
            from stations.models import Episode
            if Episode.objects.filter(url=item["url"]).exists():
                self.logger.debug(f"Skipping already scraped episode: {item['title']}")
                continue

            # Follow episode link to get full details
            self.episodes_scraped += 1
            episodes_found += 1
            yield response.follow(
                item["url"], callback=self.parse_episode_detail,
                meta={"item": item, "date_text": date_text},
            )

        self.logger.info(
            f"Scraped {episodes_found} episodes from this page. Total: {self.episodes_scraped}/{self.max_episodes}"
        )

        # Follow pagination only if we haven't reached the limit or date floor
        if self._hit_date_floor:
            self.logger.info("Date floor reached. Stopping pagination.")
            return

        if self.episodes_scraped < self.max_episodes:
            # BBC Sounds pagination: <a aria-label="View the next page" href="?page=N">
            next_page = response.css('a[aria-label="View the next page"]::attr(href)').get()
            if not next_page:
                # Fallback: numbered page links (e.g. ?page=2)
                next_page = response.css('a[href*="page="]::attr(href)').getall()
                # Pick the page after current
                current_page = 1
                current_url = response.url
                m = re.search(r'[?&]page=(\d+)', current_url)
                if m:
                    current_page = int(m.group(1))
                target = str(current_page + 1)
                next_page = next(
                    (href for href in next_page if f'page={target}' in href),
                    None
                )

            if next_page:
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.info("No more pages found.")
        else:
            self.logger.info(
                f"Reached maximum episodes limit ({self.max_episodes}). Stopping pagination."
            )

    def parse_episode_detail(self, response):
        """Parse individual episode detail page to extract full data"""
        item = response.meta.get("item", EpisodeItem())

        # Primary: date extracted from list page link text (passed via meta)
        date_text = response.meta.get("date_text")

        # Fallback: regex for a date anywhere on the detail page
        if not date_text:
            page_text = " ".join(response.css("::text").getall())
            match = re.search(
                r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}",
                page_text,
            )
            if match:
                date_text = match.group(0)

        # Extract description - look for the episode description paragraph
        description = None

        # Try to extract from JSON data first (BBC includes rich data in script tag)
        json_data_script = response.css('script#__NEXT_DATA__::text').get()
        if json_data_script:
            try:
                import json
                next_data = json.loads(json_data_script)
                # Navigate the JSON structure to find synopses
                props = next_data.get('props', {})
                page_props = props.get('pageProps', {})
                dehydrated = page_props.get('dehydratedState', {})
                queries = dehydrated.get('queries', [])

                # Look for the query with episode data
                for query in queries:
                    state_data = query.get('state', {}).get('data', {})
                    if isinstance(state_data, dict) and 'data' in state_data:
                        json_items = state_data.get('data', [])
                        for json_item in json_items:
                            if isinstance(json_item, dict) and json_item.get('type') == 'inline_display_module':
                                data_items = json_item.get('data', [])
                                for data_item in data_items:
                                    synopses = data_item.get('synopses', {})
                                    # Prefer long synopsis, fallback to medium, then short
                                    description = synopses.get('long') or synopses.get('medium') or synopses.get('short')
                                    if description:
                                        self.logger.info(f"Extracted description from JSON data: {description[:100]}...")
                                        break
                            if description:
                                break
                    if description:
                        break
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.debug(f"Could not parse JSON data: {e}")

        # Fallback to meta tag if JSON extraction failed
        if not description:
            description = response.css(
                'meta[property="og:description"]::attr(content)'
            ).get()

        # Last resort: look for description paragraphs
        if not description:
            description_selectors = [
                "p::text",
                'div[data-testid="episode-description"] p::text',
                ".episode-description::text",
            ]

            for selector in description_selectors:
                descs = response.css(selector).getall()
                # Find the first substantial paragraph (usually the episode description)
                for desc in descs:
                    if (
                        desc and len(desc.strip()) > 100
                    ):  # Episode descriptions are usually long
                        description = desc.strip()
                        break
                if description:
                    break

        # Build raw_data dictionary with all scraped information
        # Stored in Episode.scraped_data by the pipeline
        raw_data = {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "date_text": date_text,
            "description": description,
            "html_title": response.css("title::text").get(),
            "meta_tags": {
                "og_title": response.css(
                    'meta[property="og:title"]::attr(content)'
                ).get(),
                "og_description": response.css(
                    'meta[property="og:description"]::attr(content)'
                ).get(),
            },
        }

        # Store raw data in spider instance for pipeline to access
        # (Can't store in item since EpisodeItem doesn't support arbitrary fields)
        if not hasattr(self, "_raw_data_cache"):
            self._raw_data_cache = {}
        self._raw_data_cache[item.get("url", "")] = raw_data

        yield item
