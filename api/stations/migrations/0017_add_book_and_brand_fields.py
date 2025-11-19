# Generated manually for component refactor

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0016_phrase'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='book',
            name='cover_image',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='brand',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
    ]
