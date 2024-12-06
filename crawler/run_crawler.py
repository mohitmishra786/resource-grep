# crawler/crawler.py  
from scrapy.crawler import CrawlerProcess  
from scrapy.utils.project import get_project_settings  
from resource_crawler.spiders.resource_spider import ResourceSpider  
import sys  
import logging  

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

    # Initialize Scrapy process  
    process = CrawlerProcess(get_project_settings())  
    process.crawl(ResourceSpider, search_query=search_query)  
    process.start()  

if __name__ == "__main__":  
    run_crawler()  