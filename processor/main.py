#!/usr/bin/env python3
import time
import argparse
import logging
import os
import sys
import requests
from requests.exceptions import ConnectionError

# Add the processor directory to the path so we can import the ContentProcessor
sys.path.append('/app/processor')
from content_processor import ContentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_elasticsearch(host, port, max_retries=30, delay=2):
    """Wait for Elasticsearch to become available"""
    url = f"http://{host}:{port}"
    logger.info(f"Waiting for Elasticsearch at {url}")
    
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"Elasticsearch is ready at {url}")
                return True
        except ConnectionError:
            pass
        
        logger.info(f"Elasticsearch not ready yet. Retrying in {delay} seconds... ({i+1}/{max_retries})")
        time.sleep(delay)
    
    logger.error(f"Could not connect to Elasticsearch after {max_retries} attempts")
    return False

def main():
    parser = argparse.ArgumentParser(description='Process content for indexing')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    args = parser.parse_args()
    
    # Get Elasticsearch connection details from environment variables
    es_host = os.environ.get('ELASTICSEARCH_HOST', 'elasticsearch')
    es_port = int(os.environ.get('ELASTICSEARCH_PORT', 9200))
    
    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch(es_host, es_port):
        sys.exit(1)
    
    logger.info(f"Connecting to Elasticsearch at {es_host}:{es_port}")
    processor = ContentProcessor(es_host=es_host, es_port=es_port)
    
    if args.daemon:
        logger.info("Starting processor in daemon mode")
        while True:
            try:
                # In a real application, you might poll a queue or watch a directory
                # for new content to process
                logger.info("Processor running and waiting for content...")
                time.sleep(60)  # Sleep for 60 seconds before checking again
            except Exception as e:
                logger.error(f"Error in processor daemon: {e}")
                time.sleep(10)  # Sleep briefly before retrying
    else:
        logger.info("Processing content once and exiting")
        # Process any pending content and exit
        # In a real application, you might process files from a specific directory

if __name__ == "__main__":
    main()