"""
Fix episodes with NULL aired_at by re-parsing date_text from scraped_data.

Dry-run by default; pass --apply to commit changes.

Usage:
    python manage.py fix_aired_dates
    python manage.py fix_aired_dates --apply
"""

from django.core.management.base import BaseCommand
from stations.models import Episode
from stations.ai_utils import _parse_date


class Command(BaseCommand):
    help = "Fix episodes with NULL aired_at by re-parsing scraped_data date_text"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually update the database (default is dry-run)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        episodes = Episode.objects.filter(aired_at__isnull=True).order_by("id")
        total = episodes.count()

        if total == 0:
            self.stdout.write("No episodes with NULL aired_at found.")
            return

        mode = "APPLY" if apply else "DRY RUN"
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"  fix_aired_dates — {total} episodes with NULL aired_at  [{mode}]")
        self.stdout.write(f"{'=' * 60}\n")

        fixed = 0
        unfixable = []

        for ep in episodes:
            scraped = ep.scraped_data or {}
            date_text = scraped.get("date_text")
            parsed = _parse_date(date_text) if date_text else None

            if parsed:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  #{ep.id} {ep.title[:55]}  →  {parsed.strftime('%d %b %Y')}"
                    )
                )
                if apply:
                    ep.aired_at = parsed
                    ep.save(update_fields=["aired_at"])
                fixed += 1
            else:
                reason = f"date_text={date_text!r}" if date_text else "no date_text"
                self.stdout.write(
                    self.style.WARNING(
                        f"  #{ep.id} {ep.title[:55]}  —  unfixable ({reason})"
                    )
                )
                unfixable.append((ep.id, ep.title[:55], reason))

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"  Fixed: {fixed}  |  Unfixable: {len(unfixable)}  |  Total: {total}")
        if not apply and fixed > 0:
            self.stdout.write("  Run with --apply to commit changes.")
        self.stdout.write(f"{'=' * 60}\n")
