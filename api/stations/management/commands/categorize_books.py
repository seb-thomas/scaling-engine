"""Backfill book categories using Claude AI."""

import json
import os
import logging

from django.core.management.base import BaseCommand
from anthropic import Anthropic

from stations.models import Book, Category

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Categorize books that don't have categories set, using Claude AI."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0, help="Max books to process (0 = all)"
        )
        parser.add_argument(
            "--overwrite", action="store_true", help="Overwrite existing categories"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be done"
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            self.stderr.write("ANTHROPIC_API_KEY not set")
            return

        client = Anthropic(api_key=api_key)
        valid_slugs = set(Category.objects.values_list("slug", flat=True))

        queryset = Book.objects.all().order_by("id")
        if not options["overwrite"]:
            queryset = queryset.filter(categories__isnull=True)

        if options["limit"]:
            queryset = queryset[: options["limit"]]

        books = list(queryset)
        if not books:
            self.stdout.write("No books to categorize.")
            return

        self.stdout.write(f"Categorizing {len(books)} books...")

        # Batch books into groups of 20 for efficiency
        batch_size = 20
        updated = 0

        for i in range(0, len(books), batch_size):
            batch = books[i : i + batch_size]
            book_list = "\n".join(
                f'{b.id}. "{b.title}" by {b.author}'
                + (f" — {b.description[:100]}" if b.description else "")
                for b in batch
            )

            prompt = f"""Categorize each book. Return JSON only — an array of objects with "id" and "categories" (a list of slugs).

A book can have multiple categories. Available categories: fiction, classics, prize-winners, debut, history, biography, cookbooks, politics, science, arts

Books:
{book_list}

Return ONLY valid JSON array, no other text."""

            try:
                message = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = message.content[0].text.strip()
                if response_text.startswith("```"):
                    response_text = response_text.split("\n", 1)[1]
                    response_text = response_text.rsplit("```", 1)[0].strip()

                results = json.loads(response_text)
                id_to_cats = {
                    r["id"]: [c.strip().lower() for c in r["categories"]]
                    for r in results
                }

                for book in batch:
                    cat_slugs = id_to_cats.get(book.id, [])
                    valid = [s for s in cat_slugs if s in valid_slugs]
                    if valid:
                        if options["dry_run"]:
                            self.stdout.write(
                                f"  {book.title} → {', '.join(valid)}"
                            )
                        else:
                            cats = Category.objects.filter(slug__in=valid)
                            book.categories.set(cats)
                            updated += 1
                    else:
                        self.stderr.write(
                            f"  Skipping {book.title}: no valid categories"
                        )

            except Exception as e:
                self.stderr.write(f"Error processing batch: {e}")
                continue

        action = "Would categorize" if options["dry_run"] else "Categorized"
        self.stdout.write(self.style.SUCCESS(f"{action} {updated} books."))
