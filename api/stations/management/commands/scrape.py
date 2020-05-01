from django.core.management.base import BaseCommand
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from stations.models import Brand, Episode


class Command(BaseCommand):
    help = "Collect Episodes for Brand"

    def handle(self, *args, **options):
        url = Brand.objects.first().url
        result = requests.get(f"{url}/episodes/player")
        soup = BeautifulSoup(result.content, "lxml")
        h2_tags = soup.select(".programme__titles")

        for h2_tag in h2_tags:
            a_tag = h2_tag.find("a")
            url = a_tag.attrs["href"]
            name = a_tag.text

            print(url)

        #     try:
        #         Station.objects.create(url=url, name=name)
        #         print("%s added" % (name,))
        #     except:
        #         print("%s already exists" % (name,))
        # self.stdout.write("Job complete")
