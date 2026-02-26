"""Step 3 of 3: Remove old episode FK from Book."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0041_migrate_book_episode_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="book",
            name="episode",
        ),
    ]
