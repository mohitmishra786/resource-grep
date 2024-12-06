# processor/content_processor.py  
import redis  
import json  
from elasticsearch import Elasticsearch  
import time  
from concurrent.futures import ThreadPoolExecutor  
import logging  

# Configure logging  
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")  
logger = logging.getLogger(__name__)  

class ContentProcessor:  
    def __init__(self):  
        try:  
            # Initialize Redis and Elasticsearch clients  
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)  
            self.es = Elasticsearch(['http://localhost:9200'])  

            # Test connections  
            if not self.redis_client.ping():  
                raise Exception("Failed to connect to Redis")  
            if not self.es.ping():  
                raise Exception("Failed to connect to Elasticsearch")  

            logger.info("Successfully connected to Redis and Elasticsearch")  
        except Exception as e:  
            logger.error(f"Initialization error: {e}")  
            raise  

    def process_content(self, content):  
        """Process and index content from Redis into Elasticsearch."""  
        try:  
            # Parse content from Redis  
            data = json.loads(content)  
            logger.info(f"Processing content from URL: {data.get('url')}")  

            # Prepare data for Elasticsearch  
            processed_data = {  
                'url': data.get('url'),  
                'title': data.get('title', 'Untitled'),  
                'content': data.get('text', ''),  
                'code_snippets': data.get('code_blocks', []),  
                'domain': data.get('domain', 'unknown'),  
                'processed_at': time.time(),  
                'keywords': self._extract_keywords(data.get('text', '')),  
                'resource_type': self._determine_resource_type(data)  
            }  

            # Index data into Elasticsearch  
            self.es.index(index='websearch', body=processed_data, id=processed_data['url'])  
            logger.info(f"Indexed content into Elasticsearch: {processed_data['url']}")  

        except Exception as e:  
            logger.error(f"Error processing content: {e}")  

    def _extract_keywords(self, text):  
        """Extract keywords from text (basic implementation)."""  
        if not text:  
            return []  
        words = text.lower().split()  
        return list(set(words))  # Return unique words as keywords  

    def _determine_resource_type(self, data):  
        """Determine the resource type based on the domain."""  
        domain = data.get('domain', '')  
        if 'github.com' in domain:  
            return 'repository'  
        elif 'stackoverflow.com' in domain:  
            return 'qa'  
        elif 'medium.com' in domain:  
            return 'article'  
        elif 'dev.to' in domain:  
            return 'article'  
        return 'general'  

    def start_processing(self):  
        """Start consuming data from Redis and processing it."""  
        logger.info("Starting content processor...")  
        with ThreadPoolExecutor(max_workers=4) as executor:  
            while True:  
                try:  
                    # Fetch data from Redis queue  
                    content = self.redis_client.brpop('resource_queue', timeout=5)  
                    if content:  
                        logger.info("Fetched content from Redis queue")  
                        executor.submit(self.process_content, content[1])  
                    else:  
                        logger.info("No data in Redis queue. Waiting...")  
                except Exception as e:  
                    logger.error(f"Error while consuming from Redis: {e}")  
                    time.sleep(5)  # Wait before retrying  

if __name__ == "__main__":  
    processor = ContentProcessor()  
    processor.start_processing()  