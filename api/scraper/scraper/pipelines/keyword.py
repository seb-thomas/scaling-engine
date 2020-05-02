
from scrapy.exceptions import DropItem


class ContainsKeywordPipeline:
    def process_item(self, item, spider):
        if "Albert" in item["name"]:
            return item
        else:
            raise DropItem("Not in %s" % item["name"])
