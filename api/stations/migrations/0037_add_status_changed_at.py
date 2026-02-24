from django.db import migrations, models
from django.utils import timezone


def backfill_status_changed_at(apps, schema_editor):
    Episode = apps.get_model("stations", "Episode")
    # For PROCESSED/FAILED episodes, use processed_at as the last status change
    Episode.objects.filter(
        status__in=["PROCESSED", "FAILED"],
        processed_at__isnull=False,
    ).update(status_changed_at=models.F("processed_at"))
    # For everything else (SCRAPED, QUEUED, PROCESSING), set to now
    Episode.objects.filter(status_changed_at__isnull=True).update(
        status_changed_at=timezone.now()
    )


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0036_backfill_review_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="episode",
            name="status_changed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(
            backfill_status_changed_at,
            migrations.RunPython.noop,
        ),
    ]
