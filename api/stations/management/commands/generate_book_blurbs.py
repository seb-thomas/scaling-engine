import os
from django.core.management.base import BaseCommand
from anthropic import Anthropic
from stations.models import Book


class Command(BaseCommand):
    help = "Generate AI-powered micro blurbs for books (short teasers for homepage)"

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
            help="Overwrite existing blurbs",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without saving",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            self.stdout.write(
                self.style.ERROR("ANTHROPIC_API_KEY environment variable not set")
            )
            return

        client = Anthropic(api_key=api_key)
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        # Get books that need blurbs
        books = Book.objects.prefetch_related("episodes", "episodes__brand").all()

        if not overwrite:
            books = books.filter(blurb="")

        if options["limit"]:
            books = books[: options["limit"]]

        total = books.count()
        self.stdout.write(f"Processing {total} books...")

        generated = 0
        failed = 0

        for book in books:
            self.stdout.write(f"\nProcessing: {book.title} by {book.author or 'Unknown'}")

            try:
                blurb = self._generate_blurb(client, book)

                if blurb:
                    if dry_run:
                        self.stdout.write(f"  Would set blurb: {blurb}")
                    else:
                        book.blurb = blurb
                        book.save(update_fields=["blurb"])
                        self.stdout.write(self.style.SUCCESS(f"  Blurb: {blurb}"))
                    generated += 1
                else:
                    failed += 1
                    self.stdout.write(self.style.WARNING("  No blurb generated"))

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run: {generated} blurbs would be generated, {failed} failed"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nCompleted: {generated} blurbs generated, {failed} failed"
                )
            )

    def _generate_blurb(self, client: Anthropic, book: Book) -> str:
        """Generate a short, engaging blurb for a book."""
        first_ep = book.episodes.select_related("brand").first()
        show_name = first_ep.brand.name if first_ep and first_ep.brand else "a radio show"

        prompt = f"""Generate a very short, engaging blurb (max 120 characters) for this book that was featured on {show_name}.
The blurb should be intriguing and make someone want to learn more.

Book: "{book.title}"
Author: {book.author or "Unknown"}
{f'Description: {book.description[:200]}' if book.description else ''}

Write ONLY the blurb text, nothing else. No quotes. Keep it under 120 characters."""

        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )

            blurb = response.content[0].text.strip()
            # Ensure it's not too long
            if len(blurb) > 150:
                blurb = blurb[:147] + "..."
            return blurb

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  API error: {e}"))
            return ""
