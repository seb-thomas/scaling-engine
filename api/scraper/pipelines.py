# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError
from scrapy.exceptions import DropItem
from stations.models import Episode

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

            # Save episode first
            episode = item.save()
            logger.info(f"Added episode: {item['title']}")

            # Get raw data from spider's cache (stored in parse_episode_detail)
            raw_data = None
            if hasattr(spider, "_raw_data_cache"):
                episode_url = item.get("url", "")
                raw_data = spider._raw_data_cache.pop(episode_url, None)

            # Store snapshot and status on Episode
            if raw_data and episode:
                episode.scraped_data = raw_data
                episode.status = Episode.STATUS_SCRAPED
                episode.save(update_fields=["scraped_data", "status"])
                logger.info(f"Saved scraped_data for episode: {item['title']}")

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
