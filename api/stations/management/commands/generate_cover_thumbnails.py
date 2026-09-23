"""Create WebP thumbnails for book covers that don't have fresh ones yet."""

from django.core.management.base import BaseCommand

from stations.covers import generate_thumbnails
from stations.models import Book


class Command(BaseCommand):
    help = "Generate cover thumbnails (idempotent; skips covers whose thumbnails are fresh)"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Regenerate even if fresh")

    def handle(self, *args, **options):
        books = Book.objects.exclude(cover_image="").exclude(cover_image__isnull=True)
        written = covers = 0
        for book in books.iterator():
            n = generate_thumbnails(book, force=options["force"])
            if n:
                covers += 1
                written += n
        self.stdout.write(
            self.style.SUCCESS(f"Thumbnails: {written} written for {covers} covers ({books.count()} with covers)")
        )
