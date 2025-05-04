# crawler/resource_crawler/settings.py  

BOT_NAME = 'resource_crawler'  

SPIDER_MODULES = ['resource_crawler.spiders']  
NEWSPIDER_MODULE = 'resource_crawler.spiders'  

# Crawl responsibly by identifying yourself  
USER_AGENT = 'Mozilla/5.0 (compatible; ResourceCrawler/1.0; +http://example.com)'

# Obey robots.txt rules - set to False to allow more comprehensive crawling
# Note: Be respectful of website policies in production environments
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests  
CONCURRENT_REQUESTS = 128  
CONCURRENT_REQUESTS_PER_DOMAIN = 64

# Configure a delay for requests for the same website  
DOWNLOAD_DELAY = 0.1  
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

# Configure depth - increased substantially to allow deeper crawling
DEPTH_LIMIT = 12
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleLifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.LifoMemoryQueue'

# Configure retries
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Configure timeouts - increased to allow more time for responses
DOWNLOAD_TIMEOUT = 30

# Configure allowed domains - no restrictions
ALLOWED_DOMAINS = []

# Maximum number of pages to crawl per spider - increased dramatically
CLOSESPIDER_PAGECOUNT = 10000

# Maximum time the spider is allowed to run (in seconds)
CLOSESPIDER_TIMEOUT = 14400  # 4 hours

# Configure signals
SIGNALS_ENABLED = False

# Redis settings
REDIS_HOST = 'redis'
REDIS_PORT = 6379

# Elasticsearch settings 
ELASTICSEARCH_HOST = 'elasticsearch'
ELASTICSEARCH_PORT = 9200

# Real-time updates
REALTIME_UPDATES = True

# Disable auto-throttling to crawl faster
AUTOTHROTTLE_ENABLED = False

# Don't filter duplicates to ensure we don't miss content
DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'

# Increase DNS cache size
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 1000