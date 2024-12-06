# crawler/run_crawler.py  
from scrapy.crawler import CrawlerProcess  
from scrapy.utils.project import get_project_settings  
from resource_crawler.spiders.resource_spider import ResourceSpider  

def run_crawler():  
    process = CrawlerProcess(get_project_settings())  
    process.crawl(ResourceSpider)  
    process.start()  

if __name__ == "__main__":  
    run_crawler()  