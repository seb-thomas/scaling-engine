# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem


class ContainsKeywordPipeline:
    def process_item(self, item, spider):
        if "Albert" in item["name"]:
            return item
        else:
            raise DropItem("Not in %s" % item["name"])


class SaveToDbPipeline:
    def process_item(self, item, spider):
        try:
            item.save()
            print("Added %s" % item["name"])
        except:
            print("Could not add %s" % item["name"])
        return item
