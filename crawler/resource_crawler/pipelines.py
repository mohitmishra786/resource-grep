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
import hashlib
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
import redis
import json

logger = logging.getLogger(__name__)

class ResourcePipeline:
    """
    Pipeline that saves scraped resources to Elasticsearch
    """
    def __init__(self, elasticsearch_host='localhost', elasticsearch_port=9200, redis_host='redis', redis_port=6379):
        self.elasticsearch_host = elasticsearch_host
        self.elasticsearch_port = elasticsearch_port
        self.es = Elasticsearch([{'host': elasticsearch_host, 'port': elasticsearch_port, 'scheme': 'http'}])
        
        # Redis connection for real-time updates
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        
        # Check if index exists. If not, create it
        if not self.es.indices.exists(index='resources'):
            logging.info("Creating 'resources' index in Elasticsearch...")
            mappings = {
                "mappings": {
                    "properties": {
                        "url": {
                            "type": "keyword"  # Keyword for exact matching
                        },
                        "title": {
                            "type": "text"
                        },
                        "description": {
                            "type": "text"
                        },
                        "domain": {
                            "type": "keyword"
                        },
                        "type": {
                            "type": "keyword"
                        },
                        "languages": {
                            "type": "keyword"
                        },
                        "timestamp": {
                            "type": "date"
                        },
                        "content": {
                            "type": "text"
                        },
                        "code_snippets": {
                            "type": "text"
                        }
                    }
                }
            }
            self.es.indices.create(index='resources', body=mappings)
            logging.info("Index created successfully")

    def process_item(self, item, spider):
        # Create a hash of the URL to use as document ID
        url_hash = hashlib.md5(item['url'].encode()).hexdigest()
        
        # Check if the document already exists
        doc_exists = self.es.exists(index='resources', id=url_hash)
        
        # Flag to track if this is a new item
        is_new = not doc_exists
        
        if doc_exists:
            # Update existing document
            try:
                self.es.update(
                    index='resources',
                    id=url_hash,
                    body={'doc': dict(item)}
                )
                logging.info(f"Updated existing document for URL: {item['url']}")
            except Exception as e:
                logging.error(f"Error updating document: {e}")
        else:
            # Index a new document
            try:
                self.es.index(
                    index='resources',
                    id=url_hash,
                    body=dict(item)
                )
                logging.info(f"Indexed new document for URL: {item['url']}")
            except Exception as e:
                logging.error(f"Error indexing document: {e}")
        
        # Publish to Redis for real-time updates if it's a new item or search_query is specified
        if is_new or (hasattr(spider, 'search_query') and spider.search_query):
            try:
                # Prepare a simplified version of the item for real-time updates
                realtime_item = {
                    'id': url_hash,
                    'url': item['url'],
                    'title': item['title'],
                    'description': item['description'],
                    'type': item['type'],
                    'domain': item['domain'],
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add language if available
                if 'languages' in item and item['languages']:
                    realtime_item['language'] = item['languages'][0]
                
                # If spider has a search query, publish to that specific channel
                if hasattr(spider, 'search_query') and spider.search_query:
                    channel = f"search:results:{spider.search_query}"
                    self.redis_client.publish(channel, json.dumps(realtime_item))
                    logging.info(f"Published result to channel: {channel}")
                
                # Always publish to general updates channel
                self.redis_client.publish('search:results:all', json.dumps(realtime_item))
            except Exception as e:
                logging.error(f"Error publishing to Redis: {e}")
        
        return item

    @classmethod
    def from_crawler(cls, crawler):
        elasticsearch_host = crawler.settings.get('ELASTICSEARCH_HOST', 'localhost')
        elasticsearch_port = crawler.settings.get('ELASTICSEARCH_PORT', 9200)
        redis_host = crawler.settings.get('REDIS_HOST', 'redis')
        redis_port = crawler.settings.get('REDIS_PORT', 6379)
        return cls(elasticsearch_host, elasticsearch_port, redis_host, redis_port)
