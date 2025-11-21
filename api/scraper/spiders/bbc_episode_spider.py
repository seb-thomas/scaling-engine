import scrapy
from scraper.items import EpisodeItem
from stations.models import Brand


class BbcEpisodeSpider(scrapy.Spider):
    name = "bbc_episodes"

    def __init__(self, brand_id=None, max_episodes=50, *args, **kwargs):
        super(BbcEpisodeSpider, self).__init__(*args, **kwargs)
        self.max_episodes = int(max_episodes) if max_episodes else 50
        self.episodes_scraped = 0
        
        if brand_id:
            self.brand = Brand.objects.get(pk=brand_id)
        else:
            # Try to find Front Row by name, otherwise get first brand
            self.brand = Brand.objects.filter(name__icontains='Front Row').first()
            if not self.brand:
                self.brand = Brand.objects.first()

    def start_requests(self):
        if not self.brand:
            self.logger.error("No brand found. Please create a Brand first or pass brand_id parameter.")
            return

        self.logger.info(f"Scraping up to {self.max_episodes} episodes from: {self.brand.name}")

        # BBC Sounds brand page directly lists episodes - no need to add /episodes/player
        episodes_url = self.brand.url.rstrip('/')

        self.logger.info(f"Starting scrape from: {episodes_url}")
        yield scrapy.Request(url=episodes_url, callback=self.parse)

    def parse(self, response):
        # Check if we've reached the limit
        if self.episodes_scraped >= self.max_episodes:
            self.logger.info(f"Reached maximum episodes limit ({self.max_episodes}). Stopping.")
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

            # Clean up the URL
            item["url"] = url.strip() if url else ""

            # Make URL absolute if it's relative
            if item["url"] and not item["url"].startswith('http'):
                item["url"] = response.urljoin(item["url"])

            self.episodes_scraped += 1
            episodes_found += 1
            yield item

        self.logger.info(f"Scraped {episodes_found} episodes from this page. Total: {self.episodes_scraped}/{self.max_episodes}")

        # Follow pagination only if we haven't reached the limit
        if self.episodes_scraped < self.max_episodes:
            # Look for next page button
            next_page = response.css("a:contains('Next')::attr(href)").get()
            if not next_page:
                # Try alternative pagination selector
                next_page = response.css("li.pagination__next a::attr(href)").get()

            if next_page:
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.info("No more pages found.")
        else:
            self.logger.info(f"Reached maximum episodes limit ({self.max_episodes}). Stopping pagination.")
