# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy_djangoitem import DjangoItem
from stations.models import Station, Episode


class StationItem(DjangoItem):
    django_model = Station


class EpisodeItem(DjangoItem):
    django_model = Episode
