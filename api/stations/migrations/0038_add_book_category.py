from django.db import migrations, models


def seed_categories(apps, schema_editor):
    Category = apps.get_model("stations", "Category")
    categories = [
        ("Fiction", "fiction"),
        ("Classics", "classics"),
        ("Prize Winners", "prize-winners"),
        ("Debut", "debut"),
        ("History", "history"),
        ("Biography", "biography"),
        ("Cookbooks", "cookbooks"),
        ("Politics", "politics"),
        ("Science", "science"),
        ("Arts", "arts"),
    ]
    for name, slug in categories:
        Category.objects.get_or_create(slug=slug, defaults={"name": name})


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0037_add_status_changed_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120, unique=True)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="book",
            name="categories",
            field=models.ManyToManyField(blank=True, to="stations.Category"),
        ),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
