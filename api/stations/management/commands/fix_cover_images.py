"""
Fix broken cover_image paths where URLs were incorrectly stored as file paths.

This happened because cover_image was changed from URLField to ImageField,
but some code was still assigning URL strings directly instead of downloading
the images properly.
"""

from django.core.management.base import BaseCommand
from stations.models import Book


class Command(BaseCommand):
    help = "Fix broken cover_image paths (URLs stored as file paths)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be fixed without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find books where cover_image looks like a URL was stored as a path
        # These will have patterns like "https%3A" or "http%3A" or start with "http"
        broken_books = []

        for book in Book.objects.exclude(cover_image="").exclude(cover_image__isnull=True):
            cover_path = str(book.cover_image)
            # Check if it looks like a URL was stored as a path
            if (
                "http" in cover_path.lower()
                or "%3a" in cover_path.lower()  # URL-encoded colon
                or "://" in cover_path
            ):
                broken_books.append(book)

        if not broken_books:
            self.stdout.write(self.style.SUCCESS("No broken cover images found!"))
            return

        self.stdout.write(f"Found {len(broken_books)} books with broken cover_image paths:\n")

        for book in broken_books:
            self.stdout.write(f"  - {book.title}: {book.cover_image}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run: Would clear {len(broken_books)} broken cover_image paths."
                )
            )
            self.stdout.write(
                "Run 'python manage.py download_book_covers' afterwards to fetch proper images."
            )
        else:
            for book in broken_books:
                book.cover_image = ""
                book.save(update_fields=["cover_image"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nCleared {len(broken_books)} broken cover_image paths."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Run 'python manage.py download_book_covers' to fetch proper images."
                )
            )

