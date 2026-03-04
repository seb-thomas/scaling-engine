"""
Replace google_books_verified with verification_status + verification_checked_at.

Existing books get verification_status='verified' and verification_checked_at=now().
"""

from django.db import migrations, models
from django.utils import timezone


def migrate_verified_status(apps, schema_editor):
    """Set all existing books to verified (they passed Google Books check)."""
    Book = apps.get_model("stations", "Book")
    now = timezone.now()
    Book.objects.all().update(
        verification_status="verified",
        verification_checked_at=now,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("stations", "0047_rename_category_to_topic"),
    ]

    operations = [
        # Step 1: Add new fields
        migrations.AddField(
            model_name="book",
            name="verification_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("verified", "Verified"),
                    ("not_found", "Not found"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="book",
            name="verification_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Step 2: Migrate existing data
        migrations.RunPython(migrate_verified_status, migrations.RunPython.noop),
        # Step 3: Remove old field
        migrations.RemoveField(
            model_name="book",
            name="google_books_verified",
        ),
    ]
