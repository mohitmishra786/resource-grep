# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
from elasticsearch import Elasticsearch
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResourcePipeline:
    def __init__(self):
        es_host = os.environ.get('ELASTICSEARCH_HOST', 'elasticsearch')
        es_port = int(os.environ.get('ELASTICSEARCH_PORT', 9200))
        self.es = Elasticsearch([f'http://{es_host}:{es_port}'])
        
        # Create index if it doesn't exist
        if not self.es.indices.exists(index='resources'):
            self.es.indices.create(
                index='resources',
                mappings={
                    "properties": {
                        "url": {"type": "keyword"},
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "domain": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "languages": {"type": "keyword"},
                        "timestamp": {"type": "date"}
                    }
                }
            )

    def process_item(self, item, spider):
        try:
            # Index the document
            self.es.index(index='resources', document=dict(item))
            logger.info(f"Successfully indexed: {item.get('title', 'No title')}")
        except Exception as e:
            logger.error(f"Failed to index item: {str(e)}")
        return item
