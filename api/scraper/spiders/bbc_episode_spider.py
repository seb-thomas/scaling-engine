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
        
        # Construct the episodes URL - BBC Sounds uses /episodes/player endpoint
        base_url = self.brand.url.rstrip('/')
        if '/brand/' in base_url:
            # URL format: https://www.bbc.co.uk/sounds/brand/b006qnlr
            episodes_url = f"{base_url}/episodes/player?page=1"
        else:
            # Fallback: try appending /episodes/player
            episodes_url = f"{base_url}/episodes/player?page=1"
        
        self.logger.info(f"Starting scrape from: {episodes_url}")
        yield scrapy.Request(url=episodes_url, callback=self.parse)

    def parse(self, response):
        # Check if we've reached the limit
        if self.episodes_scraped >= self.max_episodes:
            self.logger.info(f"Reached maximum episodes limit ({self.max_episodes}). Stopping.")
            return

        episodes_found = 0
        for episode in response.css("div.programme--episode"):
            if self.episodes_scraped >= self.max_episodes:
                break
                
            item = EpisodeItem()
            titles = episode.css(".programme__titles")
            title_text = titles.css("*::text").get()
            url = titles.css("a::attr(href)").get()
            
            if not title_text or not url:
                continue
                
            # Clean up the title and URL
            item["title"] = title_text.strip()
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
            next_page = response.css("li.pagination__next a::attr(href)").get()
            if next_page:
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.info("No more pages found.")
        else:
            self.logger.info(f"Reached maximum episodes limit ({self.max_episodes}). Stopping pagination.")
