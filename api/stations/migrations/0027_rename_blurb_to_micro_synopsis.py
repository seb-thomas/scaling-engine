# Generated manually for blurb -> micro_synopsis rename

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0026_simplify_book_cover_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='book',
            old_name='blurb',
            new_name='micro_synopsis',
        ),
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
