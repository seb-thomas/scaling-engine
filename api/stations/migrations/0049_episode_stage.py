"""
Replace Episode.status + Episode.review_status with a single Episode.stage field.

1. Expand status choices to include all new stage values
2. Data migration: map old status+review_status combos to new stages
3. Remove review_status field
4. Rename status → stage
5. Set final choices on stage
"""

from django.db import migrations, models


def migrate_status_to_stage(apps, schema_editor):
    Episode = apps.get_model("stations", "Episode")

    # SCRAPED → SCRAPED (no change needed)
    # QUEUED → EXTRACTION_QUEUED
    Episode.objects.filter(status="QUEUED").update(status="EXTRACTION_QUEUED")
    # PROCESSING → EXTRACTING
    Episode.objects.filter(status="PROCESSING").update(status="EXTRACTING")
    # FAILED → EXTRACTION_FAILED
    Episode.objects.filter(status="FAILED").update(status="EXTRACTION_FAILED")

    # PROCESSED episodes — map based on review_status and has_book
    # PROCESSED + has_book=False → EXTRACTION_NO_BOOKS
    Episode.objects.filter(status="PROCESSED", has_book=False).update(
        status="EXTRACTION_NO_BOOKS"
    )
    # PROCESSED + review_status=NOT_REQUIRED → COMPLETE
    Episode.objects.filter(status="PROCESSED", review_status="NOT_REQUIRED").update(
        status="COMPLETE"
    )
    # PROCESSED + review_status=REQUIRED → REVIEW
    Episode.objects.filter(status="PROCESSED", review_status="REQUIRED").update(
        status="REVIEW"
    )
    # PROCESSED + review_status=REVIEWED → COMPLETE
    Episode.objects.filter(status="PROCESSED", review_status="REVIEWED").update(
        status="COMPLETE"
    )
    # Remaining PROCESSED (review_status="" with has_book=True) → VERIFICATION_QUEUED
    Episode.objects.filter(status="PROCESSED").update(status="VERIFICATION_QUEUED")


def reverse_migration(apps, schema_editor):
    Episode = apps.get_model("stations", "Episode")

    # Reverse: map stages back to old status + review_status
    Episode.objects.filter(status="EXTRACTION_QUEUED").update(status="QUEUED")
    Episode.objects.filter(status="EXTRACTING").update(status="PROCESSING")
    Episode.objects.filter(status="EXTRACTION_FAILED").update(status="FAILED")
    Episode.objects.filter(status="EXTRACTION_NO_BOOKS").update(status="PROCESSED")
    Episode.objects.filter(status="VERIFICATION_QUEUED").update(status="PROCESSED")
    Episode.objects.filter(status="VERIFICATION_FAILED").update(status="PROCESSED")
    Episode.objects.filter(status="REVIEW").update(
        status="PROCESSED", review_status="REQUIRED"
    )
    Episode.objects.filter(status="COMPLETE").update(
        status="PROCESSED", review_status="NOT_REQUIRED"
    )


ALL_STAGE_CHOICES = [
    # Old values (needed during migration)
    ("SCRAPED", "Scraped"),
    ("QUEUED", "Queued"),
    ("PROCESSING", "Processing"),
    ("PROCESSED", "Processed"),
    ("FAILED", "Failed"),
    # New values
    ("EXTRACTION_QUEUED", "Extraction Queued"),
    ("EXTRACTING", "Extracting"),
    ("EXTRACTION_NO_BOOKS", "No Books Found"),
    ("EXTRACTION_FAILED", "Extraction Failed"),
    ("VERIFICATION_QUEUED", "Verification Queued"),
    ("VERIFICATION_FAILED", "Verification Failed"),
    ("REVIEW", "Needs Review"),
    ("COMPLETE", "Complete"),
]

FINAL_STAGE_CHOICES = [
    ("SCRAPED", "Scraped"),
    ("EXTRACTION_QUEUED", "Extraction Queued"),
    ("EXTRACTING", "Extracting"),
    ("EXTRACTION_NO_BOOKS", "No Books Found"),
    ("EXTRACTION_FAILED", "Extraction Failed"),
    ("VERIFICATION_QUEUED", "Verification Queued"),
    ("VERIFICATION_FAILED", "Verification Failed"),
    ("REVIEW", "Needs Review"),
    ("COMPLETE", "Complete"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0048_book_verification_status"),
    ]

    operations = [
        # 1. Expand choices and max_length on status to accommodate all values
        migrations.AlterField(
            model_name="episode",
            name="status",
            field=models.CharField(
                choices=ALL_STAGE_CHOICES,
                default="SCRAPED",
                max_length=25,
            ),
        ),
        # 2. Data migration
        migrations.RunPython(migrate_status_to_stage, reverse_migration),
        # 3. Remove review_status
        migrations.RemoveField(
            model_name="episode",
            name="review_status",
        ),
        # 4. Rename status → stage
        migrations.RenameField(
            model_name="episode",
            old_name="status",
            new_name="stage",
        ),
        # 5. Final choices on stage
        migrations.AlterField(
            model_name="episode",
            name="stage",
            field=models.CharField(
                choices=FINAL_STAGE_CHOICES,
                default="SCRAPED",
                max_length=25,
            ),
        ),
    ]
