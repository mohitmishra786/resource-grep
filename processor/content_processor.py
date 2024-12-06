# processor/content_processor.py  
import redis  
import json  
from elasticsearch import Elasticsearch  
import time  
from concurrent.futures import ThreadPoolExecutor  
import logging  

logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  

class ContentProcessor:  
    def __init__(self):  
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)  
        self.es = Elasticsearch(['http://localhost:9200'])  

    def process_content(self, content):  
        try:  
            # Parse content  
            data = json.loads(content)  

            # Process and enrich content  
            processed_data = {  
                'url': data['url'],  
                'title': data['title'],  
                'content': data['text'],  
                'code_snippets': data['code_blocks'],  
                'domain': data['domain'],  
                'processed_at': time.time(),  
                'keywords': self._extract_keywords(data['text']),  
                'resource_type': self._determine_resource_type(data)  
            }  

            # Index in Elasticsearch  
            self.es.index(  
                index='websearch',  
                body=processed_data,  
                id=processed_data['url']  
            )  

            logger.info(f"Processed and indexed content from: {data['url']}")  

        except Exception as e:  
            logger.error(f"Error processing content: {e}")  

    def _extract_keywords(self, text):  
        # Add keyword extraction logic here  
        # For now, return simple word frequency  
        words = text.lower().split()  
        return list(set(words))  

    def _determine_resource_type(self, data):  
        # Determine type based on URL and content  
        if 'github.com' in data['domain']:  
            return 'repository'  
        elif 'stackoverflow.com' in data['domain']:  
            return 'qa'  
        elif 'medium.com' in data['domain']:  
            return 'article'  
        return 'general'  

    def start_processing(self):  
        logger.info("Starting content processor...")  
        with ThreadPoolExecutor(max_workers=4) as executor:  
            while True:  
                # Get content from Redis queue  
                content = self.redis_client.brpop('resource_queue', timeout=1)  
                if content:  
                    executor.submit(self.process_content, content[1])  