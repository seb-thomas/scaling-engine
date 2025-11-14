# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class ContainsKeywordPipeline:
    def process_item(self, item, spider):
        if "Albert" in item["name"]:
            return item
        else:
            raise DropItem("Not in %s" % item["name"])


class SaveToDbPipeline:
    def process_item(self, item, spider):
        try:
            item["brand"] = spider.brand
            item.save()
            logger.info(f"Added episode: {item['title']}")
        except IntegrityError as e:
            # Duplicate entry (URL already exists) - this is expected, just skip
            logger.debug(f"Episode already exists: {item['title']} - {e}")
        except ValidationError as e:
            # Data validation failed - log and skip
            logger.error(f"Validation error for episode {item['title']}: {e}")
        except DatabaseError as e:
            # Database connection issues - log and re-raise to trigger retry
            logger.error(f"Database error while saving {item['title']}: {e}")
            raise
        except Exception as e:
            # Unexpected error - log with full context and re-raise
            logger.exception(f"Unexpected error saving episode {item['title']}: {e}")
            raise
        return item
