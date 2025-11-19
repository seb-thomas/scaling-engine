from django.core.management.base import BaseCommand
from stations.models import Book
from stations.utils import fetch_book_cover


class Command(BaseCommand):
    help = 'Populate book cover images from Open Library API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of books to process',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing cover images',
        )

    def handle(self, *args, **options):
        books = Book.objects.all()
        
        if not options['overwrite']:
            books = books.filter(cover_image='')
        
        if options['limit']:
            books = books[:options['limit']]
        
        total = books.count()
        self.stdout.write(f'Processing {total} books...')
        
        updated = 0
        failed = 0
        
        for book in books:
            self.stdout.write(f'Processing: {book.title} by {book.author or "Unknown"}')
            
            cover_url = fetch_book_cover(book.title, book.author)
            
            if cover_url:
                book.cover_image = cover_url
                book.save(update_fields=['cover_image'])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Found cover: {cover_url}'))
            else:
                failed += 1
                self.stdout.write(self.style.WARNING(f'  ✗ No cover found'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted: {updated} updated, {failed} not found, {total} total'
        ))

