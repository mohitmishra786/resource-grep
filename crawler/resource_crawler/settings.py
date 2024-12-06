# crawler/resource_crawler/settings.py  

BOT_NAME = 'resource_crawler'  

SPIDER_MODULES = ['resource_crawler.spiders']  
NEWSPIDER_MODULE = 'resource_crawler.spiders'  

# Crawl responsibly by identifying yourself  
USER_AGENT = 'ResourceCrawler (+http://www.yourdomain.com)'  

# Obey robots.txt rules  
ROBOTSTXT_OBEY = True  

# Configure maximum concurrent requests  
CONCURRENT_REQUESTS = 16  

# Configure a delay for requests for the same website  
DOWNLOAD_DELAY = 1  

# Disable cookies  
COOKIES_ENABLED = False  

# Enable and configure HTTP caching  
HTTPCACHE_ENABLED = True  
HTTPCACHE_EXPIRATION_SECS = 0  
HTTPCACHE_DIR = 'httpcache'  
HTTPCACHE_IGNORE_HTTP_CODES = []  
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'  