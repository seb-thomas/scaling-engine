"""Rename Category → Topic, categories → topics, unmatched_categories → unmatched_topics.
Also seed the 'Arts' topic (was in AI prompt but missing from DB)."""

from django.db import migrations


def create_arts_topic(apps, schema_editor):
    Topic = apps.get_model("stations", "Topic")
    Topic.objects.get_or_create(slug="arts", defaults={"name": "Arts"})


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0046_populate_station_brand_data"),
    ]

    operations = [
        migrations.RenameModel(old_name="Category", new_name="Topic"),
        migrations.RenameField(
            model_name="book", old_name="categories", new_name="topics"
        ),
        migrations.RenameField(
            model_name="book",
            old_name="unmatched_categories",
            new_name="unmatched_topics",
        ),
        migrations.RunPython(create_arts_topic, migrations.RunPython.noop),
    ]
