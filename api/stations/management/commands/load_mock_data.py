"""
Load mock data for development
Based on the Figma Make design with rich content
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from stations.models import Station, Brand, Episode, Book


class Command(BaseCommand):
    help = 'Load mock data for development (based on Figma design)'

    def handle(self, *args, **options):
        self.stdout.write('Loading mock data...\n')

        # Create BBC Radio 4 Station
        bbc, _ = Station.objects.get_or_create(
            station_id='bbc',
            defaults={
                'name': 'BBC Radio 4',
                'url': 'https://www.bbc.co.uk/sounds/brand/b006qnlr'
            }
        )
        self.stdout.write(f'✓ Station: {bbc.name}')

        # Create NPR Station
        npr, _ = Station.objects.get_or_create(
            station_id='npr',
            defaults={
                'name': 'NPR',
                'url': 'https://www.npr.org/'
            }
        )
        self.stdout.write(f'✓ Station: {npr.name}')

        # Create BBC Shows (Brands)
        front_row, _ = Brand.objects.get_or_create(
            station=bbc,
            name='Front Row',
            defaults={
                'url': 'https://www.bbc.co.uk/sounds/brand/b006qnlr',
                'description': "BBC Radio 4's daily arts and culture programme, featuring the latest books, films, theatre, and visual arts"
            }
        )
        self.stdout.write(f'  ✓ Brand: {front_row.name}')

        bookclub, _ = Brand.objects.get_or_create(
            station=bbc,
            name='Bookclub',
            defaults={
                'url': 'https://www.bbc.co.uk/sounds/brand/p00fzl7j',
                'description': 'A monthly books discussion programme where listeners and authors meet to discuss a contemporary or classic work'
            }
        )
        self.stdout.write(f'  ✓ Brand: {bookclub.name}')

        saturday_review, _ = Brand.objects.get_or_create(
            station=bbc,
            name='Saturday Review',
            defaults={
                'url': 'https://www.bbc.co.uk/sounds/brand/b007n1dw',
                'description': 'Weekly roundup of the latest cultural releases across literature, film, music, and theatre'
            }
        )
        self.stdout.write(f'  ✓ Brand: {saturday_review.name}')

        # Create NPR Shows
        fresh_air, _ = Brand.objects.get_or_create(
            station=npr,
            name='Fresh Air',
            defaults={
                'url': 'https://www.npr.org/programs/fresh-air',
                'description': "Interviews with today's most compelling personalities, including in-depth conversations with authors"
            }
        )
        self.stdout.write(f'  ✓ Brand: {fresh_air.name}')

        all_things, _ = Brand.objects.get_or_create(
            station=npr,
            name='All Things Considered',
            defaults={
                'url': 'https://www.npr.org/programs/all-things-considered',
                'description': "NPR's flagship news and culture program featuring book reviews and author interviews"
            }
        )
        self.stdout.write(f'  ✓ Brand: {all_things.name}')

        # Create Episodes and Books with rich Figma content
        books_data = [
            {
                'brand': front_row,
                'episode_title': 'The Art of Game Design in Literature',
                'episode_date': datetime(2024, 11, 15, tzinfo=ZoneInfo('UTC')),
                'book_title': 'Tomorrow, and Tomorrow, and Tomorrow',
                'book_author': 'Gabrielle Zevin',
                'book_description': 'A novel about two friends who build video games together, exploring creativity, identity, and the profound connections between art and life.',
                'book_cover': 'https://images.unsplash.com/photo-1610882648335-ced8fc8fa6b6?w=400'
            },
            {
                'brand': fresh_air,
                'episode_title': "Abraham Verghese's Epic Family Saga",
                'episode_date': datetime(2024, 11, 14, tzinfo=ZoneInfo("UTC")),
                'book_title': 'The Covenant of Water',
                'book_author': 'Abraham Verghese',
                'book_description': 'A sweeping, magical novel spanning three generations of a family in South India, bound by a peculiar family secret.',
                'book_cover': 'https://images.unsplash.com/photo-1758279771969-2cc6bcac3fd1?w=400'
            },
            {
                'brand': all_things,
                'episode_title': 'Stephen King Returns with Holly Gibney',
                'episode_date': datetime(2024, 11, 13, tzinfo=ZoneInfo("UTC")),
                'book_title': 'Holly',
                'book_author': 'Stephen King',
                'book_description': "Stephen King's detective Holly Gibney takes on a new case involving a pair of mysterious professors in a thriller that confronts our current moment.",
                'book_cover': 'https://images.unsplash.com/photo-1696947833843-9707b58254fa?w=400'
            },
            {
                'brand': front_row,
                'episode_title': 'Celebrity Memoirs and Truth-Telling',
                'episode_date': datetime(2024, 11, 12, tzinfo=ZoneInfo("UTC")),
                'book_title': 'The Woman in Me',
                'book_author': 'Britney Spears',
                'book_description': 'A brave and astonishingly moving memoir about freedom, fame, motherhood, survival, faith, and hope.',
                'book_cover': 'https://images.unsplash.com/photo-1619878473858-ace2b236897c?w=400'
            },
            {
                'brand': bookclub,
                'episode_title': "James McBride's Portrait of a Community",
                'episode_date': datetime(2024, 11, 11, tzinfo=ZoneInfo("UTC")),
                'book_title': 'The Heaven & Earth Grocery Store',
                'book_author': 'James McBride',
                'book_description': 'A richly colorful portrait of a community in a small town in Pennsylvania, where Jewish and Black families forge deep bonds of friendship in the face of prejudice.',
                'book_cover': 'https://images.unsplash.com/photo-1611576673788-a954e01092d1?w=400'
            },
            {
                'brand': saturday_review,
                'episode_title': "Zadie Smith's Victorian Mystery",
                'episode_date': datetime(2024, 11, 10, tzinfo=ZoneInfo("UTC")),
                'book_title': 'The Fraud',
                'book_author': 'Zadie Smith',
                'book_description': 'A historical novel set in Victorian England, centered around a famous trial and the search for truth.',
                'book_cover': 'https://images.unsplash.com/photo-1723220217588-3fc2fb87b69a?w=400'
            },
            {
                'brand': fresh_air,
                'episode_title': 'A House Through the Centuries',
                'episode_date': datetime(2024, 11, 7, tzinfo=ZoneInfo("UTC")),
                'book_title': 'North Woods',
                'book_author': 'Daniel Mason',
                'book_description': 'A novel that follows a single house in New England through three centuries, told through the lives of its inhabitants and the natural world around it.',
                'book_cover': 'https://images.unsplash.com/photo-1758279771969-2cc6bcac3fd1?w=400'
            },
            {
                'brand': bookclub,
                'episode_title': 'Family Dysfunction and Irish Humor',
                'episode_date': datetime(2024, 11, 6, tzinfo=ZoneInfo("UTC")),
                'book_title': 'The Bee Sting',
                'book_author': 'Paul Murray',
                'book_description': 'A darkly comic novel about a family in rural Ireland dealing with financial collapse and buried secrets.',
                'book_cover': 'https://images.unsplash.com/photo-1696947833843-9707b58254fa?w=400'
            },
            {
                'brand': all_things,
                'episode_title': 'Dystopia and Motherhood',
                'episode_date': datetime(2024, 11, 5, tzinfo=ZoneInfo("UTC")),
                'book_title': 'Our Missing Hearts',
                'book_author': 'Celeste Ng',
                'book_description': 'A dystopian novel about a mother who leaves her family to protect them, and the son who searches for her.',
                'book_cover': 'https://images.unsplash.com/photo-1610882648335-ced8fc8fa6b6?w=400'
            },
            {
                'brand': fresh_air,
                'episode_title': 'Reimagining Dickens in Appalachia',
                'episode_date': datetime(2024, 11, 3, tzinfo=ZoneInfo("UTC")),
                'book_title': 'Demon Copperhead',
                'book_author': 'Barbara Kingsolver',
                'book_description': 'A retelling of David Copperfield set in modern-day Appalachia, exploring poverty and resilience.',
                'book_cover': 'https://images.unsplash.com/photo-1758279771969-2cc6bcac3fd1?w=400'
            },
            {
                'brand': front_row,
                'episode_title': 'Women in Science and Unexpected Careers',
                'episode_date': datetime(2024, 11, 2, tzinfo=ZoneInfo("UTC")),
                'book_title': 'Lessons in Chemistry',
                'book_author': 'Bonnie Garmus',
                'book_description': 'A debut novel about a chemist in the 1960s who becomes an unlikely cooking show star.',
                'book_cover': 'https://images.unsplash.com/photo-1611576673788-a954e01092d1?w=400'
            },
            {
                'brand': bookclub,
                'episode_title': 'Friendship and Coming of Age',
                'episode_date': datetime(2024, 10, 31, tzinfo=ZoneInfo("UTC")),
                'book_title': 'The Rachel Incident',
                'book_author': "Caroline O'Donoghue",
                'book_description': 'A sharp, funny novel about friendship, first love, and what it means to grow up in Ireland.',
                'book_cover': 'https://images.unsplash.com/photo-1610882648335-ced8fc8fa6b6?w=400'
            },
        ]

        created_count = 0
        for data in books_data:
            # Create episode
            episode, ep_created = Episode.objects.get_or_create(
                brand=data['brand'],
                title=data['episode_title'],
                defaults={
                    'url': f"https://example.com/episode/{data['episode_title'].lower().replace(' ', '-')}",
                    'aired_at': data['episode_date'],
                    'has_book': True
                }
            )

            # Create book
            book, book_created = Book.objects.get_or_create(
                episode=episode,
                title=data['book_title'],
                defaults={
                    'author': data['book_author'],
                    'description': data['book_description'],
                    'cover_image': data['book_cover']
                }
            )

            if book_created:
                created_count += 1
                self.stdout.write(f'    ✓ Book: {book.title} by {book.author}')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Loaded {created_count} new books with rich content!'))
        self.stdout.write(self.style.SUCCESS(f'📚 Total books: {Book.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'📺 Total shows: {Brand.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'\nVisit http://localhost:8001 to see your new components in action! 🚀'))
