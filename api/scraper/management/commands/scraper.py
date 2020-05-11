from django.core.management.base import BaseCommand
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scraper.spiders.quotes_spider import QuotesSpider


class Command(BaseCommand):
    help = "Run Scraper"

    def handle(self, *args, **options):
        process = CrawlerProcess(get_project_settings())

        process.crawl(QuotesSpider)
        process.start()
