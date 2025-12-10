import os
import tempfile
import urllib.request
from django.core.management.base import BaseCommand
from django.core.files import File
from stations.models import Book
from stations.utils import fetch_book_cover


class Command(BaseCommand):
    help = "Fetch book covers from Open Library and store them locally"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of books to process",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing covers",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be downloaded without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        # Get books
        if overwrite:
            books = Book.objects.all()
        else:
            # Only process books without covers
            books = Book.objects.filter(cover_image="") | Book.objects.filter(
                cover_image__isnull=True
            )

        if options["limit"]:
            books = books[: options["limit"]]

        total = books.count()
        self.stdout.write(f"Processing {total} books...")

        downloaded = 0
        failed = 0
        skipped = 0

        for book in books:
            # Skip if already has cover and not overwriting
            if book.cover_image and not overwrite:
                skipped += 1
                continue

            self.stdout.write(f"Processing: {book.title} by {book.author or 'Unknown'}")

            # Fetch cover URL from Open Library
            cover_url = fetch_book_cover(book.title, book.author)
            if not cover_url:
                self.stdout.write(self.style.WARNING(f"  No cover found"))
                failed += 1
                continue

            if dry_run:
                self.stdout.write(f"  Would download: {cover_url}")
                downloaded += 1
                continue

            try:
                # Download the image
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg"
                ) as tmp_file:
                    request = urllib.request.Request(
                        cover_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; RadioReads/1.0)"
                        },
                    )

                    with urllib.request.urlopen(request, timeout=30) as response:
                        tmp_file.write(response.read())
                        tmp_path = tmp_file.name

                # Save to the model
                filename = f"{book.slug}.jpg"
                with open(tmp_path, "rb") as f:
                    book.cover_image.save(filename, File(f), save=True)

                # Clean up temp file
                os.unlink(tmp_path)

                downloaded += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Downloaded: {book.cover_image.url}")
                )

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run: {downloaded} books would be processed, {skipped} skipped, {failed} no cover found"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nCompleted: {downloaded} downloaded, {failed} failed/no cover, {skipped} skipped"
                )
            )
