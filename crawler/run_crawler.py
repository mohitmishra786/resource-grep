# crawler/run_crawler.py
"""
Standalone crawler runner script.

This script runs the ResourceSpider in standalone mode.
For distributed crawling, see the coordinator service instead.
"""  
import os
import sys
import logging  
import uuid
import subprocess
from scrapy.utils.project import get_project_settings  
from scrapy.utils.log import configure_logging
from resource_crawler.spiders.resource_spider import ResourceSpider  

# Configure logging  
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")  
logger = logging.getLogger(__name__)  

def run_crawler():  
    # Get the search query from command-line arguments  
    if len(sys.argv) < 2:  
        logger.error("Please provide a search query as an argument.")  
        sys.exit(1)  

    search_query = sys.argv[1]  
    logger.info(f"Starting crawler with search query: {search_query}")  

    # Run scrapy crawl command
    subprocess.Popen([
        'scrapy', 'crawl',
        'resource_spider',
        '-a', f'search_query={search_query}'
    ])

# Function to be called from the API
def start_crawler(seed_urls=None, search_query=None):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Use provided search_query or default to "python"
    query = search_query if search_query else "python"
    
    # Create command
    cmd = ['scrapy', 'crawl', 'resource_spider', '-a', f'search_query={query}']
    if seed_urls:
        cmd.extend(['-a', f'start_urls={",".join(seed_urls)}'])
    
    # Add logging of the query
    logger.info(f"Starting crawler job {job_id} with query: {query}")
    
    # Run scrapy crawl command
    subprocess.Popen(cmd)
    
    return job_id

if __name__ == "__main__":  
    run_crawler()  