import scrapy  
from scrapy.spiders import CrawlSpider, Rule  
from scrapy.linkextractors import LinkExtractor  
from urllib.parse import urlparse, quote  
import json  
import redis  
from datetime import datetime  
import logging  
from bs4 import BeautifulSoup  
import re  

logging.basicConfig(  
    filename='crawler.log',  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
    level=logging.INFO  
)  

class ResourceSpider(CrawlSpider):  
    name = 'resource_spider'  

    # These will be overridden in __init__ with search query  
    start_urls = []  

    # Custom settings for the spider  
    custom_settings = {  
        'ROBOTSTXT_OBEY': True,  
        'CONCURRENT_REQUESTS': 16,  
        'DOWNLOAD_DELAY': 1,  
        'COOKIES_ENABLED': False,  
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  
        'DOWNLOAD_TIMEOUT': 15,  
        'RETRY_TIMES': 3,  
        'DEPTH_LIMIT': 3,  
    }  

    # Define rules for link extraction  
    rules = (  
        # Follow search result pages  
        Rule(  
            LinkExtractor(  
                allow=(  
                    r'/search\?',  
                    r'/page/\d+',  
                    r'\?page=\d+',  
                )  
            ),  
            follow=True  
        ),  
        # Extract content from matching pages  
        Rule(  
            LinkExtractor(  
                allow=(  
                    r'github\.com/[^/]+/[^/]+$',  # GitHub repositories  
                    r'stackoverflow\.com/questions/\d+',  # Stack Overflow questions  
                    r'dev\.to/[^/]+/[^/]+$',  # Dev.to articles  
                    r'medium\.com/[^/]+/[^/]+$',  # Medium articles  
                )  
            ),  
            callback='parse_resource',  
            follow=True  
        ),  
    )  

    def __init__(self, search_query=None, *args, **kwargs):  
        super(ResourceSpider, self).__init__(*args, **kwargs)  
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)  
        self.search_query = search_query  

        # Encode search query for URLs  
        encoded_query = quote(search_query) if search_query else ''  

        # Define start URLs based on search query  
        self.start_urls = [  
            f'https://github.com/search?q={encoded_query}&type=repositories',  
            f'https://dev.to/search?q={encoded_query}',  
            f'https://stackoverflow.com/search?q={encoded_query}',  
            f'https://medium.com/search?q={encoded_query}',  
        ]  

        logging.info(f"Initialized spider with search query: {search_query}")  
        logging.info(f"Start URLs: {self.start_urls}")  

    def parse_resource(self, response):  
        """Parse different types of resources based on domain"""  
        try:  
            domain = urlparse(response.url).netloc  
            content = None  

            if 'github.com' in domain:  
                content = self.parse_github(response)  
            elif 'stackoverflow.com' in domain:  
                content = self.parse_stackoverflow(response)  
            elif 'dev.to' in domain:  
                content = self.parse_devto(response)  
            elif 'medium.com' in domain:  
                content = self.parse_medium(response)  

            if content:  
                # Add common fields  
                content.update({  
                    'url': response.url,  
                    'domain': domain,  
                    'timestamp': datetime.now().isoformat(),  
                    'search_query': self.search_query  
                })  

                # Store in Redis for real-time processing  
                self.redis_client.lpush('resource_queue', json.dumps(content))  
                logging.info(f"Successfully parsed and queued: {response.url}")  

                return content  

        except Exception as e:  
            logging.error(f"Error parsing {response.url}: {str(e)}")  
            return None  

    def parse_github(self, response):  
        """Parse GitHub repository pages"""  
        try:  
            # Extract repository information  
            return {  
                'title': response.css('h1.d-flex::text').get('').strip(),  
                'description': response.css('.f4.my-3::text').get('').strip(),  
                'stars': response.css('a.social-count::text').get('').strip(),  
                'language': response.css('span[itemprop="programmingLanguage"]::text').get(''),  
                'readme': ' '.join(response.css('article.markdown-body ::text').getall()),  
                'code_blocks': response.css('pre::text, code::text').getall(),  
                'resource_type': 'github_repository'  
            }  
        except Exception as e:  
            logging.error(f"Error parsing GitHub page {response.url}: {str(e)}")  
            return None  

    def parse_stackoverflow(self, response):  
        """Parse Stack Overflow question pages"""  
        try:  
            return {  
                'title': response.css('h1[itemprop="name"] a::text').get('').strip(),  
                'question': ' '.join(response.css('div.question div.post-text ::text').getall()),  
                'answers': [  
                    ' '.join(answer.css('.answer-text ::text').getall())  
                    for answer in response.css('div.answer')  
                ],  
                'code_blocks': response.css('pre code::text').getall(),  
                'tags': response.css('div.post-taglist a::text').getall(),  
                'resource_type': 'stackoverflow_qa'  
            }  
        except Exception as e:  
            logging.error(f"Error parsing Stack Overflow page {response.url}: {str(e)}")  
            return None  

    def parse_devto(self, response):  
        """Parse Dev.to article pages"""  
        try:  
            return {  
                'title': response.css('h1#article-show-title::text').get('').strip(),  
                'content': ' '.join(response.css('div#article-body ::text').getall()),  
                'tags': response.css('div.tags a::text').getall(),  
                'code_blocks': response.css('div.highlight ::text').getall(),  
                'author': response.css('a.user-profile-link::text').get('').strip(),  
                'resource_type': 'devto_article'  
            }  
        except Exception as e:  
            logging.error(f"Error parsing Dev.to page {response.url}: {str(e)}")  
            return None  

    def parse_medium(self, response):  
        """Parse Medium article pages"""  
        try:  
            return {  
                'title': response.css('h1::text').get('').strip(),  
                'content': ' '.join(response.css('article ::text').getall()),  
                'claps': response.css('button.clap-button::text').get('0').strip(),  
                'author': response.css('a[rel="author"]::text').get('').strip(),  
                'tags': response.css('a.tag::text').getall(),  
                'resource_type': 'medium_article'  
            }  
        except Exception as e:  
            logging.error(f"Error parsing Medium page {response.url}: {str(e)}")  
            return None  

    def clean_text(self, text):  
        """Clean and normalize text content"""  
        if not text:  
            return ''  
        # Remove extra whitespace and normalize  
        text = re.sub(r'\s+', ' ', text.strip())  
        # Remove special characters but keep basic punctuation  
        text = re.sub(r'[^\w\s.,!?-]', '', text)  
        return text  

    def closed(self, reason):  
        """Called when the spider is closed"""  
        logging.info(f"Spider closed: {reason}")  
        self.redis_client.close()  