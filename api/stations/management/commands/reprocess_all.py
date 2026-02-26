"""
Reprocess all episodes through AI extraction (synchronous, diagnostic).

Runs extraction one-by-one with full output per episode so you can
monitor results, catch errors, and spot patterns.

Usage:
    python manage.py reprocess_all
    python manage.py reprocess_all --status FAILED    # only failed ones
    python manage.py reprocess_all --dry-run           # show what would run
"""

import time
from django.core.management.base import BaseCommand
from stations.models import Episode, Book


class Command(BaseCommand):
    help = "Reprocess all episodes through AI extraction (synchronous, with diagnostics)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            type=str,
            default=None,
            help="Only reprocess episodes with this status (e.g. FAILED, PROCESSED)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be reprocessed without actually running extraction",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Max number of episodes to process",
        )

    def handle(self, *args, **options):
        qs = Episode.objects.all().order_by("id")
        if options["status"]:
            qs = qs.filter(status=options["status"])

        if options["limit"]:
            qs = qs[: options["limit"]]

        episodes = list(qs)
        total = len(episodes)

        if total == 0:
            self.stdout.write("No episodes to process.")
            return

        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write(f"  REPROCESS ALL — {total} episodes")
        self.stdout.write(f"{'=' * 70}\n")

        if options["dry_run"]:
            for ep in episodes:
                book_count = ep.books.count()
                self.stdout.write(
                    f"  [{ep.status:10}] #{ep.id} {ep.title[:60]}"
                    f"  ({book_count} books)"
                )
            self.stdout.write(f"\nDry run — {total} episodes would be reprocessed.")
            return

        from stations.ai_utils import extract_books_from_episode

        stats = {
            "processed": 0,
            "failed": 0,
            "errors": [],
            "books_before": 0,
            "books_after": 0,
            "changes": [],
        }

        start_time = time.time()

        for i, ep in enumerate(episodes, 1):
            old_books = set(
                ep.books.values_list("title", flat=True)
            )
            stats["books_before"] += len(old_books)

            self.stdout.write(f"\n[{i}/{total}] #{ep.id} {ep.title[:65]}")
            self.stdout.write(f"  Status: {ep.status} | Old books: {sorted(old_books) or '(none)'}")

            try:
                result = extract_books_from_episode(ep.id)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  EXCEPTION: {e}"))
                stats["failed"] += 1
                stats["errors"].append((ep.id, ep.title[:50], str(e)))
                continue

            ep.refresh_from_db()
            new_books = set(
                ep.books.values_list("title", flat=True)
            )
            stats["books_after"] += len(new_books)

            reasoning = (result.get("reasoning") or "")[:200]
            self.stdout.write(f"  Result: has_book={result.get('has_book')} | New books: {sorted(new_books) or '(none)'}")
            self.stdout.write(f"  Reasoning: {reasoning}")

            if ep.status == Episode.STATUS_FAILED:
                stats["failed"] += 1
                stats["errors"].append((ep.id, ep.title[:50], ep.last_error or "unknown"))
                self.stdout.write(self.style.ERROR(f"  FAILED: {ep.last_error}"))
            else:
                stats["processed"] += 1

            # Track changes
            removed = old_books - new_books
            added = new_books - old_books
            if removed or added:
                change = {"id": ep.id, "title": ep.title[:50]}
                if removed:
                    change["removed"] = sorted(removed)
                if added:
                    change["added"] = sorted(added)
                stats["changes"].append(change)
                if removed:
                    self.stdout.write(self.style.WARNING(f"  REMOVED: {sorted(removed)}"))
                if added:
                    self.stdout.write(self.style.SUCCESS(f"  ADDED: {sorted(added)}"))

        elapsed = time.time() - start_time

        # Summary
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write(f"  SUMMARY")
        self.stdout.write(f"{'=' * 70}")
        self.stdout.write(f"  Total:     {total}")
        self.stdout.write(f"  OK:        {stats['processed']}")
        self.stdout.write(f"  Failed:    {stats['failed']}")
        self.stdout.write(f"  Books before: {stats['books_before']}")
        self.stdout.write(f"  Books after:  {stats['books_after']}")
        self.stdout.write(f"  Time:      {elapsed:.1f}s ({elapsed/total:.1f}s per episode)")

        if stats["changes"]:
            self.stdout.write(f"\n  CHANGES ({len(stats['changes'])}):")
            for ch in stats["changes"]:
                self.stdout.write(f"    #{ch['id']} {ch['title']}")
                if "removed" in ch:
                    self.stdout.write(self.style.WARNING(f"      - {ch['removed']}"))
                if "added" in ch:
                    self.stdout.write(self.style.SUCCESS(f"      + {ch['added']}"))

        if stats["errors"]:
            self.stdout.write(f"\n  ERRORS ({len(stats['errors'])}):")
            for eid, title, err in stats["errors"]:
                self.stdout.write(self.style.ERROR(f"    #{eid} {title}: {err}"))

        self.stdout.write(f"\n{'=' * 70}\n")
