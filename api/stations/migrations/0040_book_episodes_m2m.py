"""Step 1 of 3: Add episodes M2M field to Book (keeping old episode FK)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0039_category_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="episodes",
            field=models.ManyToManyField(
                blank=True, related_name="books", to="stations.episode"
            ),
        ),
    ]
