"""Step 2 of 3: Copy episode FK into episodes M2M for every Book."""

from django.db import migrations


def copy_fk_to_m2m(apps, schema_editor):
    Book = apps.get_model("stations", "Book")
    for book in Book.objects.select_related("episode").all():
        if book.episode_id:
            book.episodes.add(book.episode_id)


def copy_m2m_to_fk(apps, schema_editor):
    """Reverse: pick first episode from M2M and set as FK."""
    Book = apps.get_model("stations", "Book")
    for book in Book.objects.all():
        first = book.episodes.first()
        if first:
            book.episode_id = first.pk
            book.save(update_fields=["episode_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0040_book_episodes_m2m"),
    ]

    operations = [
        migrations.RunPython(copy_fk_to_m2m, copy_m2m_to_fk),
    ]
