# crawler/spider.py  
import scrapy  
from scrapy.spiders import CrawlSpider, Rule  
from scrapy.linkextractors import LinkExtractor  
from urllib.parse import urlparse  
import json  
import redis  

class ResourceSpider(CrawlSpider):  
    name = 'resource_spider'  

    # Start with popular resource sites  
    start_urls = [  
        'https://github.com/topics',  
        'https://dev.to',  
        'https://stackoverflow.com',  
        'https://medium.com/topics/programming',  
    ]  

    rules = (  
        Rule(  
            LinkExtractor(),  
            callback='parse_resource',  
            follow=True  
        ),  
    )  

    def __init__(self):  
        super(ResourceSpider, self).__init__()  
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)  

    def parse_resource(self, response):  
        # Extract domain to categorize content  
        domain = urlparse(response.url).netloc  

        # Extract relevant content based on domain-specific selectors  
        content = {  
            'url': response.url,  
            'title': response.css('title::text').get(),  
            'text': ' '.join(response.css('p::text').getall()),  
            'code_blocks': response.css('pre::text, code::text').getall(),  
            'domain': domain,  
            'timestamp': datetime.now().isoformat()  
        }  

        # Store in Redis for real-time processing  
        self.redis_client.lpush('resource_queue', json.dumps(content))  

        return content  