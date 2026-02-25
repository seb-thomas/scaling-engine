from django.db import migrations, models


def seed_descriptions(apps, schema_editor):
    Category = apps.get_model("stations", "Category")
    descriptions = {
        "fiction": "Contemporary and literary fiction from acclaimed authors",
        "classics": "Timeless works of literature revisited and rediscovered",
        "prize-winners": "Award-winning books recognised by major literary prizes",
        "debut": "Exciting first works from emerging voices in literature",
        "history": "Explorations of the past that illuminate the present",
        "biography": "Lives examined — memoirs, biographies, and personal histories",
        "cookbooks": "Food writing, recipes, and culinary journeys",
        "politics": "Political writing, commentary, and current affairs",
        "science": "Science writing that makes complex ideas accessible",
        "arts": "Books about art, music, culture, and creativity",
    }
    for slug, desc in descriptions.items():
        Category.objects.filter(slug=slug).update(description=desc)


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0038_add_book_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(seed_descriptions, migrations.RunPython.noop),
    ]
