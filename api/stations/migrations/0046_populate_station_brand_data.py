from django.db import migrations


def populate_data(apps, schema_editor):
    Station = apps.get_model("stations", "Station")
    Brand = apps.get_model("stations", "Brand")

    # Station descriptions
    station_descriptions = {
        "bbc_radio_4": (
            "BBC Radio 4 is a British national radio station owned and operated "
            "by the BBC, specialising in intelligent speech programming including "
            "literature and the arts."
        ),
        "npr": (
            "National Public Radio \u2014 American public radio network with "
            "acclaimed cultural programming and in-depth book coverage."
        ),
    }
    for sid, desc in station_descriptions.items():
        Station.objects.filter(station_id=sid).update(description=desc)

    # Brand producer fields
    producer_data = {
        "fresh-air": ("WHYY", "https://whyy.org"),
        "the-book-show": ("WAMC", "https://www.wamc.org"),
    }
    for slug, (name, url) in producer_data.items():
        Brand.objects.filter(slug=slug).update(
            producer_name=name, producer_url=url
        )

    # Shorten NPR brand descriptions
    brand_descriptions = {
        "fresh-air": (
            "Daily interviews on books, politics, music, and culture, "
            "hosted by Terry Gross and Tonya Mosley."
        ),
        "book-of-the-day": (
            "A daily recommendation of one great book, with a short "
            "review and interview excerpt."
        ),
        "the-book-show": (
            "In-depth author interviews about new and notable books, "
            "hosted by Joe Donahue."
        ),
        "code-switch": (
            "Conversations about race, identity, and culture in America, "
            "often featuring authors and their books."
        ),
    }
    for slug, desc in brand_descriptions.items():
        Brand.objects.filter(slug=slug).update(description=desc)


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0045_add_station_description_brand_producer"),
    ]

    operations = [
        migrations.RunPython(populate_data, migrations.RunPython.noop),
    ]
