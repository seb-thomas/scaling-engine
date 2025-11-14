import scrapy
from scraper.items import EpisodeItem
from stations.models import Brand


class BbcEpisodeSpider(scrapy.Spider):
    name = "bbc_episodes"

    def __init__(self, brand_id=None, *args, **kwargs):
        super(BbcEpisodeSpider, self).__init__(*args, **kwargs)
        if brand_id:
            self.brand = Brand.objects.get(pk=brand_id)
        else:
            self.brand = Brand.objects.first()

    def start_requests(self):
        if not self.brand:
            self.logger.error("No brand found. Please create a Brand first or pass brand_id parameter.")
            return
        urls = [
            f"{self.brand.url}/episodes/player?page=1",
            # "http://www.google.com"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for episode in response.css("div.programme--episode"):
            item = EpisodeItem()
            titles = episode.css(".programme__titles")
            item["title"] = titles.css("*::text").get()
            item["url"] = titles.css("a::attr(href)").get()
            yield item

        # yield from response.follow_all(css="li.pagination__next a", callback=self.parse)
