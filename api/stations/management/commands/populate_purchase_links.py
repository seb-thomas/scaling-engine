from django.core.management.base import BaseCommand
from stations.models import Book
from stations.utils import generate_bookshop_affiliate_url


class Command(BaseCommand):
    help = 'Populate Bookshop.org affiliate purchase links for books that don\'t have them'

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
            help='Overwrite existing purchase links',
        )

    def handle(self, *args, **options):
        books = Book.objects.all()
        
        if not options['overwrite']:
            books = books.filter(purchase_link='')
        
        if options['limit']:
            books = books[:options['limit']]
        
        total = books.count()
        self.stdout.write(f'Processing {total} books...')
        
        updated = 0
        
        for book in books:
            self.stdout.write(f'Processing: {book.title} by {book.author or "Unknown"}')
            
            purchase_url = generate_bookshop_affiliate_url(book.title, book.author)
            book.purchase_link = purchase_url
            book.save(update_fields=['purchase_link'])
            updated += 1
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated link: {purchase_url}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted: {updated} books updated, {total} total'
        ))

