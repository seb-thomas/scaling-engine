import os
import tempfile
import urllib.request
from django.core.management.base import BaseCommand
from django.core.files import File
from stations.models import Book


class Command(BaseCommand):
    help = "Download book covers from remote URLs and store them locally"

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
            help="Overwrite existing local covers",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be downloaded without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        # Get books with remote cover URLs
        books = Book.objects.exclude(cover_image="").exclude(cover_image__isnull=True)

        if not overwrite:
            # Only process books without local covers
            books = books.filter(cover_image_local="") | books.filter(
                cover_image_local__isnull=True
            )

        if options["limit"]:
            books = books[: options["limit"]]

        total = books.count()
        self.stdout.write(f"Processing {total} books...")

        downloaded = 0
        failed = 0
        skipped = 0

        for book in books:
            # Skip if already has local cover and not overwriting
            if book.cover_image_local and not overwrite:
                skipped += 1
                continue

            remote_url = book.cover_image
            if not remote_url:
                skipped += 1
                continue

            self.stdout.write(f"Processing: {book.title}")

            if dry_run:
                self.stdout.write(f"  Would download: {remote_url}")
                downloaded += 1
                continue

            try:
                # Download the image
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg"
                ) as tmp_file:
                    # Add headers to avoid being blocked
                    request = urllib.request.Request(
                        remote_url,
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
                    book.cover_image_local.save(filename, File(f), save=True)

                # Clean up temp file
                os.unlink(tmp_path)

                downloaded += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Downloaded: {book.cover_image_local.url}")
                )

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run: {downloaded} books would be processed, {skipped} skipped"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nCompleted: {downloaded} downloaded, {failed} failed, {skipped} skipped"
                )
            )
