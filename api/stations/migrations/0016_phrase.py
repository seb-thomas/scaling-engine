# Generated by Django 3.1a1 on 2020-05-19 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0015_auto_20200519_1751'),
    ]

    operations = [
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
            ],
        ),
    ]
