"""
Clear mock data and scrape 50 episodes from Front Row
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from stations.models import Station, Brand, Episode, Book
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.bbc_episode_spider import BbcEpisodeSpider


class Command(BaseCommand):
    help = 'Clear mock data and scrape 50 episodes from Front Row'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-clear',
            action='store_true',
            help='Skip clearing mock data',
        )

    def handle(self, *args, **options):
        # Step 1: Clear mock data (unless skipped)
        if not options['skip_clear']:
            self.stdout.write('Clearing mock data...')
            episode_count = Episode.objects.count()
            book_count = Book.objects.count()
            
            if episode_count > 0 or book_count > 0:
                # Delete books first (they have foreign key to episodes)
                deleted_books = Book.objects.all().delete()[0]
                self.stdout.write(f'✓ Deleted {deleted_books} books')
                
                # Delete episodes
                deleted_episodes = Episode.objects.all().delete()[0]
                self.stdout.write(f'✓ Deleted {deleted_episodes} episodes')
            else:
                self.stdout.write('No mock data to clear.')
        else:
            self.stdout.write('Skipping mock data clearing...')

        # Step 2: Ensure BBC Radio 4 station exists
        bbc, _ = Station.objects.get_or_create(
            station_id='bbc',
            defaults={
                'name': 'BBC Radio 4',
                'url': 'https://www.bbc.co.uk/sounds/brand/b006qnlr'
            }
        )
        self.stdout.write(f'✓ Station: {bbc.name}')

        # Step 3: Ensure Front Row brand exists
        front_row, created = Brand.objects.get_or_create(
            station=bbc,
            name='Front Row',
            defaults={
                'url': 'https://www.bbc.co.uk/sounds/brand/b006qnlr',
                'description': "BBC Radio 4's daily arts and culture programme, featuring the latest books, films, theatre, and visual arts"
            }
        )
        if created:
            self.stdout.write(f'✓ Created brand: {front_row.name}')
        else:
            self.stdout.write(f'✓ Found existing brand: {front_row.name}')

        # Step 4: Scrape 50 episodes
        self.stdout.write(f'\nScraping 50 episodes from Front Row...')
        self.stdout.write(f'Brand ID: {front_row.id}')
        self.stdout.write(f'Brand URL: {front_row.url}\n')

        try:
            settings = get_project_settings()
            settings['LOG_LEVEL'] = 'INFO'
            
            process = CrawlerProcess(settings)
            process.crawl(BbcEpisodeSpider, brand_id=front_row.id, max_episodes=50)
            process.start()
            
            # Check results
            episode_count = Episode.objects.filter(brand=front_row).count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Scraping complete!\n'
                    f'   Episodes scraped: {episode_count}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during scraping: {e}')
            )
            raise

