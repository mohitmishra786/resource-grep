"""
DistributedResourceSpider - Distributed Crawler Implementation

This spider is used by the coordinator service (coordinator/coordinator.py) for distributed crawling.
Multiple instances of this spider can be run in parallel, managed by the coordinator.

For standalone crawling, see resource_spider.py instead.
"""

import scrapy
from resource_crawler.items import ResourceItem
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import logging
import json
import redis
from scrapy.utils.project import get_project_settings
import hashlib

logger = logging.getLogger(__name__)

class DistributedResourceSpider(scrapy.Spider):
    name = "distributed_resource_spider"
    
    # Get allowed domains from settings
    settings = get_project_settings()
    allowed_domains = settings.get('ALLOWED_DOMAINS', [])
    
    # Default start URLs
    default_start_urls = [
        'https://github.com/topics/python',
        'https://stackoverflow.com/questions/tagged/python',
        'https://dev.to/t/python',
        'https://www.reddit.com/r/Python/',
        'https://www.geeksforgeeks.org/python-programming-language/',
        'https://realpython.com/tutorials/all/',
        'https://www.w3schools.com/python/',
        'https://docs.python.org/3/tutorial/',
        # React-related URLs
        'https://reactjs.org/docs/getting-started.html',
        'https://github.com/topics/react',
        'https://stackoverflow.com/questions/tagged/reactjs',
        'https://dev.to/t/react',
        'https://www.reddit.com/r/reactjs/',
        'https://www.w3schools.com/react/',
        # React Hooks specifically
        'https://reactjs.org/docs/hooks-intro.html',
        'https://reactjs.org/docs/hooks-overview.html',
        'https://reactjs.org/docs/hooks-state.html',
        'https://reactjs.org/docs/hooks-effect.html',
        # JavaScript
        'https://javascript.info/',
        'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
        'https://www.w3schools.com/js/',
        # General programming
        'https://github.com/topics/programming',
        'https://news.ycombinator.com/',
        'https://dev.to/',
    ]
    
    def __init__(self, search_query=None, start_urls=None, worker_id=None, *args, **kwargs):
        super(DistributedResourceSpider, self).__init__(*args, **kwargs)
        self.search_query = search_query
        self.worker_id = worker_id or 'default'
        
        # Redis connection
        redis_host = self.settings.get('REDIS_HOST', 'redis')
        redis_port = self.settings.get('REDIS_PORT', 6379)
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        
        # Use distributed URL queue if available
        self.start_urls = self.get_start_urls(start_urls)
        
        logger.info(f"Initialized distributed spider {self.worker_id} with search query: {search_query}")
        logger.info(f"Starting URLs: {self.start_urls[:5]}...")
    
    def get_start_urls(self, start_urls=None):
        """Get URLs from Redis queue or use provided ones"""
        # Check if there are URLs in Redis
        urls_key = f'crawler:pending_urls:{self.worker_id}'
        urls = self.redis_client.lrange(urls_key, 0, -1)
        
        if urls:
            # Get a batch of URLs from Redis
            batch_size = self.settings.get('BATCH_SIZE', 10)
            batch_urls = []
            for _ in range(min(batch_size, len(urls))):
                url = self.redis_client.lpop(urls_key)
                if url:
                    batch_urls.append(url.decode('utf-8'))
            return batch_urls
        
        # If no URLs in Redis, use provided start_urls or defaults
        if start_urls:
            if isinstance(start_urls, str):
                return start_urls.split(',')
            elif isinstance(start_urls, (list, tuple)):
                return list(start_urls)
        
        # Use default URLs
        return self.default_start_urls
    
    def parse(self, response):
        # Store this URL as visited
        self.mark_url_visited(response.url)
        
        # Extract links to follow
        for link in response.css('a::attr(href)').getall():
            full_url = response.urljoin(link)
            if self.should_follow(full_url):
                # Add URL to Redis queue for distributed processing
                self.enqueue_url(full_url)
        
        # Check if page contains valuable resources
        if self.is_resource_page(response):
            resource = self.extract_resource(response)
            if resource:
                # Publish resource for real-time updates
                self.publish_resource(resource)
                yield resource
    
    def enqueue_url(self, url):
        """Add URL to Redis queue if not already processed"""
        # Generate URL hash for deduplication
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Check if URL was already processed
        if not self.redis_client.sismember('crawler:visited_urls', url_hash):
            # Add to pending queue
            self.redis_client.rpush('crawler:pending_urls', url)
            # Mark as seen but not yet processed
            self.redis_client.sadd('crawler:seen_urls', url_hash)
    
    def mark_url_visited(self, url):
        """Mark URL as fully processed"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self.redis_client.sadd('crawler:visited_urls', url_hash)
    
    def publish_resource(self, resource):
        """Publish resource to Redis for real-time processing"""
        resource_data = {
            'url': resource['url'],
            'title': resource['title'],
            'description': resource['description'],
            'type': resource['type'],
            'language': resource['languages'][0] if resource['languages'] else None,
            'timestamp': resource['timestamp']
        }
        
        # Publish to Redis channel for real-time updates
        if self.search_query:
            # Only publish if the resource matches the search query
            search_terms = self.search_query.lower().split()
            content = (resource['title'] + ' ' + resource['description']).lower()
            
            if all(term in content for term in search_terms):
                # Calculate relevance score
                score = sum(content.count(term) for term in search_terms)
                resource_data['score'] = score
                
                # Publish to search-specific channel
                channel = f'search:results:{self.search_query}'
                self.redis_client.publish(channel, json.dumps(resource_data))
        
        # Also publish to a general channel for all new resources
        self.redis_client.publish('crawler:new_resources', json.dumps(resource_data))
    
    def should_follow(self, url):
        # Define rules for which URLs to follow
        # Avoid irrelevant pages, focus on content-rich areas
        relevant_patterns = [
            r'tutorial', r'guide', r'doc', r'example', r'resource', 
            r'learn', r'library', r'framework', r'tool', r'cheatsheet',
            r'python', r'javascript', r'react', r'node', r'web', r'code',
            r'programming', r'develop'
        ]
        
        # Check if URL matches any relevant pattern
        if any(re.search(pattern, url, re.I) for pattern in relevant_patterns):
            # Check if URL is from allowed domains
            domain = urlparse(url).netloc
            if any(allowed in domain for allowed in self.allowed_domains):
                return True
        return False
    
    def is_resource_page(self, response):
        # Detect if a page contains valuable resources
        resource_indicators = [
            response.css('pre'), response.css('code'),
            response.xpath('//h1[contains(text(), "Guide")]'),
            response.xpath('//h1[contains(text(), "Tutorial")]'),
            response.css('article'), response.css('.markdown-body'),
            response.css('.documentation'), response.css('.tutorial'),
            response.css('.content-body'), response.css('.post-content')
        ]
        
        # Check for programming keywords in title
        title = response.css('title::text').get() or ''
        programming_keywords = ['python', 'javascript', 'js', 'react', 'node', 'code', 'programming', 'tutorial', 'guide']
        has_programming_title = any(keyword in title.lower() for keyword in programming_keywords)
        
        return has_programming_title or any(indicator for indicator in resource_indicators)
    
    def extract_resource(self, response):
        resource = ResourceItem()
        
        # Extract domain to categorize content
        domain = urlparse(response.url).netloc
        
        # Extract title and description
        title = response.css('title::text').get() or response.css('h1::text').get()
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        description = meta_desc if meta_desc else ' '.join(response.css('p::text').getall()[:3])
        
        # Skip if no meaningful content
        if not title or not description:
            return None
            
        # Clean up title and description
        title = ' '.join(title.split())
        description = ' '.join(description.split())
        
        # Detect programming language
        languages = ['python', 'javascript', 'java', 'cpp', 'c++', 'ruby', 'php', 'golang', 'rust', 'typescript', 'react']
        detected_languages = [lang for lang in languages if lang.lower() in (title + ' ' + description).lower()]
        
        # If search query is provided, only process content related to that query
        if self.search_query and self.search_query.lower() not in (title + ' ' + description).lower():
            return None
        
        # Extract main content based on common content containers
        content_selectors = [
            'article', '.markdown-body', '.post-content',
            '#content', '.content', 'main', '.article-content',
            '.documentation', '.tutorial-content'
        ]
        
        content = None
        for selector in content_selectors:
            content = response.css(f'{selector}::text').getall()
            if content:
                content = ' '.join(content)
                break
        
        # Extract code snippets
        code_snippets = []
        for code_block in response.css('pre code::text').getall():
            code_snippets.append(code_block)
        
        # Extract tags/keywords
        tags = response.css('meta[name="keywords"]::attr(content)').get()
        
        # Determine resource type
        resource_type = 'article'  # default
        if 'tutorial' in title.lower() or 'guide' in title.lower():
            resource_type = 'tutorial'
        elif 'video' in title.lower() or 'youtube' in domain:
            resource_type = 'video'
        elif 'documentation' in title.lower() or 'docs' in domain:
            resource_type = 'documentation'
        elif '/github.com/' in response.url:
            resource_type = 'repository'
        elif any(doc in response.url for doc in ['docs', 'documentation', 'reference']):
            resource_type = 'documentation'
        elif any(tut in response.url for tut in ['tutorial', 'guide', 'how-to']):
            resource_type = 'tutorial'
        
        # Calculate quality score (simple algorithm)
        quality_factors = {
            'has_code': 1 if code_snippets else 0,
            'content_length': min(1.0, len(description) / 500),
            'has_tags': 1 if tags else 0,
            'domain_authority': 0.5 if any(domain in response.url for domain in ['github.com', 'stackoverflow.com', 'mdn', 'w3schools', 'reactjs.org']) else 0
        }
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        # Create resource item
        resource['url'] = response.url
        resource['title'] = title
        resource['description'] = description
        resource['content'] = content
        resource['code_snippets'] = code_snippets
        resource['tags'] = tags
        resource['domain'] = domain
        resource['type'] = resource_type
        resource['languages'] = detected_languages
        resource['timestamp'] = datetime.now().isoformat()
        resource['quality_score'] = quality_score
        
        logger.info(f"Found resource: {title} ({resource_type})")
        return resource 