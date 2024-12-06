from scrapy.crawler import CrawlerProcess  
from scrapy.utils.project import get_project_settings  
from resource_crawler.spiders.resource_spider import ResourceSpider  
import sys  

def run_crawler():  
    search_query = sys.argv[1] if len(sys.argv) > 1 else None  
    process = CrawlerProcess(get_project_settings())  
    process.crawl(ResourceSpider, search_query=search_query)  
    process.start()  

if __name__ == "__main__":  
    run_crawler()  