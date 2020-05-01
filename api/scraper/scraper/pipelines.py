# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem


class ScraperPipeline:
    def process_item(self, item, spider):
        if item.get("text"):
            if "better" in item["text"]:
                return item
            else:
                raise DropItem("Not in %s" % item["author"])
