# Generated by Django 3.1a1 on 2020-05-19 16:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0014_auto_20200519_1750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='brand',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='stations.brand'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='has_book',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
