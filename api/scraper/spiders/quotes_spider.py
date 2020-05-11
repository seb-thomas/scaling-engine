import scrapy
from scraper.items import StationItem


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def start_requests(self):
        urls = [
            "http://quotes.toscrape.com/page/1/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for quote in response.css("div.quote"):
            item = StationItem()
            item["name"] = quote.css("small.author::text").get()
            item["url"] = quote.css("div.tags a.tag::attr(href)").get()
            yield item

        # yield from response.follow_all(css="ul.pager a", callback=self.parse)
