# crawler/resource_crawler/settings.py  

BOT_NAME = 'resource_crawler'  

SPIDER_MODULES = ['resource_crawler.spiders']  
NEWSPIDER_MODULE = 'resource_crawler.spiders'  

# Crawl responsibly by identifying yourself  
USER_AGENT = 'Mozilla/5.0 (compatible; ResourceCrawler/1.0; +http://example.com)'

# Obey robots.txt rules  
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests  
CONCURRENT_REQUESTS = 16  
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure a delay for requests for the same website  
DOWNLOAD_DELAY = 1  
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies  
COOKIES_ENABLED = False  

# Enable and configure HTTP caching  
HTTPCACHE_ENABLED = True  
HTTPCACHE_EXPIRATION_SECS = 0  
HTTPCACHE_DIR = 'httpcache'  
HTTPCACHE_IGNORE_HTTP_CODES = []  
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'  

# Configure item pipelines
ITEM_PIPELINES = {
    'resource_crawler.pipelines.ResourcePipeline': 300,
}

# Configure logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# Configure depth
DEPTH_LIMIT = 3
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleLifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.LifoMemoryQueue'

# Configure retries
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Configure timeouts
DOWNLOAD_TIMEOUT = 15

# Configure allowed domains
ALLOWED_DOMAINS = [
    'geeksforgeeks.org',
    'realpython.com',
    'python.org',
    'w3schools.com',
    'github.com',
]

# Configure signals
SIGNALS_ENABLED = False