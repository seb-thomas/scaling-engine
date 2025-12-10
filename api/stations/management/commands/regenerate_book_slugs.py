from django.core.management.base import BaseCommand
from django.utils.text import slugify
from stations.models import Book


class Command(BaseCommand):
    help = "Regenerate book slugs to include author names (e.g., alan-hollinghurst-the-line-of-beauty)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        books = Book.objects.all()
        updated_count = 0

        for book in books:
            # Generate new slug with author
            if book.author:
                slug_source = f"{book.author} {book.title}"
            else:
                slug_source = book.title

            new_base_slug = slugify(slug_source) or f"book-{book.id}"

            # Check if slug would change
            if book.slug != new_base_slug and not book.slug.startswith(new_base_slug):
                old_slug = book.slug

                # Ensure uniqueness
                new_slug = new_base_slug
                counter = 1
                while Book.objects.filter(slug=new_slug).exclude(pk=book.pk).exists():
                    new_slug = f"{new_base_slug}-{counter}"
                    counter += 1

                if dry_run:
                    self.stdout.write(f"  {old_slug} -> {new_slug}")
                else:
                    book.slug = new_slug
                    book.save(update_fields=["slug"])
                    self.stdout.write(f"  {old_slug} -> {new_slug}")

                updated_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\nDry run: {updated_count} books would be updated")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nUpdated {updated_count} book slugs")
            )
