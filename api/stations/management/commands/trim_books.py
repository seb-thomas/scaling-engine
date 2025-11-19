from django.core.management.base import BaseCommand
from stations.models import Book
from django.db.models import Count


class Command(BaseCommand):
    help = 'Trim down books data to a manageable number for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=100,
            help='Number of books to keep (default: 100)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        keep_count = options['keep']
        dry_run = options['dry_run']
        
        # Get total count
        total_books = Book.objects.count()
        self.stdout.write(f'Total books in database: {total_books}')
        
        if total_books <= keep_count:
            self.stdout.write(self.style.SUCCESS(
                f'Database already has {total_books} books (≤ {keep_count}), nothing to trim.'
            ))
            return
        
        # Keep the most recent books (by episode ID, which should correlate with recency)
        books_to_keep = Book.objects.select_related('episode').order_by('-episode__id')[:keep_count]
        keep_ids = set(books_to_keep.values_list('id', flat=True))
        
        # Delete the rest
        books_to_delete = Book.objects.exclude(id__in=keep_ids)
        delete_count = books_to_delete.count()
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN: Would delete {delete_count} books, keeping {keep_count} most recent.'
            ))
            # Show some examples
            sample = books_to_delete[:5]
            self.stdout.write('Sample books that would be deleted:')
            for book in sample:
                self.stdout.write(f'  - {book.title} by {book.author or "Unknown"} (ID: {book.id})')
        else:
            self.stdout.write(f'Deleting {delete_count} books, keeping {keep_count} most recent...')
            deleted_count, _ = books_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(
                f'Deleted {deleted_count} books. {keep_count} books remaining.'
            ))

