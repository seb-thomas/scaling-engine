from django.core.management.base import BaseCommand
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from stations.models import Station


class Command(BaseCommand):
    help = "Collect Station titles"

    def handle(self, *args, **options):
        result = requests.get("https://www.whitehouse.gov/briefings-statements/")
        src = result.content
        soup = BeautifulSoup(src, "lxml")
        h2_tags = soup.find_all("h2")

        for h2_tag in h2_tags:
            a_tag = h2_tag.find("a")
            url = a_tag.attrs["href"]
            name = a_tag.text

            try:
                Station.objects.create(url=url, name=name)
                print("%s added" % (name,))
            except:
                print("%s already exists" % (name,))
        self.stdout.write("Job complete")
