# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError
from scrapy.exceptions import DropItem
from stations.models import RawEpisodeData

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

            # Save raw data to RawEpisodeData if available
            if raw_data and episode:
                # Create or update RawEpisodeData
                raw_episode_data, created = RawEpisodeData.objects.get_or_create(
                    episode=episode, defaults={"scraped_data": raw_data}
                )
                if not created:
                    # Update existing raw data
                    raw_episode_data.scraped_data = raw_data
                    raw_episode_data.processed = False
                    raw_episode_data.save()
                    logger.info(f"Updated raw data for episode: {item['title']}")
                else:
                    logger.info(f"Created raw data for episode: {item['title']}")

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
