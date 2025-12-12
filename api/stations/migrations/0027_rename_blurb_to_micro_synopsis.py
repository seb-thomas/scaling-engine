# Generated manually for blurb -> micro_synopsis rename

from django.db import migrations, models


def truncate_blurbs(apps, schema_editor):
    """Truncate existing blurb values to 40 chars before column resize."""
    Book = apps.get_model('stations', 'Book')
    for book in Book.objects.all():
        if book.blurb and len(book.blurb) > 40:
            book.blurb = book.blurb[:40]
            book.save(update_fields=['blurb'])


def noop(apps, schema_editor):
    """Reverse migration does nothing - data is already truncated."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0026_simplify_book_cover_image'),
    ]

    operations = [
        # First truncate existing data
        migrations.RunPython(truncate_blurbs, noop),
        # Then rename the field
        migrations.RenameField(
            model_name='book',
            old_name='blurb',
            new_name='micro_synopsis',
        ),
        # Finally resize the column
        migrations.AlterField(
            model_name='book',
            name='micro_synopsis',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Ultra-short AI-generated hook (35-40 chars)',
                max_length=40,
            ),
        ),
    ]
