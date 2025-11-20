"""
Clear mock data from the database
Removes all Episodes and Books, but keeps Stations and Brands
"""
from django.core.management.base import BaseCommand
from stations.models import Episode, Book


class Command(BaseCommand):
    help = 'Clear mock data (Episodes and Books) from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        episode_count = Episode.objects.count()
        book_count = Book.objects.count()

        if episode_count == 0 and book_count == 0:
            self.stdout.write(self.style.WARNING('No mock data to clear.'))
            return

        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    f'This will delete {episode_count} episodes and {book_count} books.\n'
                    'Stations and Brands will be preserved.\n'
                )
            )
            confirm = input('Are you sure? Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Delete books first (they have foreign key to episodes)
        deleted_books = Book.objects.all().delete()[0]
        self.stdout.write(f'✓ Deleted {deleted_books} books')

        # Delete episodes
        deleted_episodes = Episode.objects.all().delete()[0]
        self.stdout.write(f'✓ Deleted {deleted_episodes} episodes')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully cleared mock data!\n'
                f'   Episodes deleted: {deleted_episodes}\n'
                f'   Books deleted: {deleted_books}'
            )
        )

