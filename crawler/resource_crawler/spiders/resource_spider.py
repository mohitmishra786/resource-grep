"""
ResourceSpider - Standalone Spider Implementation

This spider is used by the standalone crawler service (run_crawler.py).
It's configured in the crawler/Dockerfile and runs as a single instance.

For distributed crawling, see distributed_spider.py instead.
"""

import scrapy
from resource_crawler.items import ResourceItem
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import logging
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)

class ResourceSpider(scrapy.Spider):
    name = "resource_spider"
    
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
        # Add React-related URLs
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
    ]
    
    def __init__(self, search_query=None, start_urls=None, *args, **kwargs):
        super(ResourceSpider, self).__init__(*args, **kwargs)
        self.search_query = search_query
        
        # Use search query to build better starting URLs if provided
        if search_query:
            logger.info(f"Initializing spider with search query: {search_query}")
            
            # Add specific search URLs for different sites based on the query
            search_specific_urls = [
                f'https://github.com/topics/{search_query}',
                f'https://stackoverflow.com/questions/tagged/{search_query}',
                f'https://dev.to/t/{search_query}',
                f'https://www.geeksforgeeks.org/search/{search_query}',
                f'https://www.google.com/search?q={search_query}+programming+tutorial',
                f'https://www.bing.com/search?q={search_query}+programming+guide',
                f'https://duckduckgo.com/?q={search_query}+programming'
            ]
            
            # Handle start URLs from command line
            if start_urls:
                if isinstance(start_urls, str):
                    self.start_urls = start_urls.split(',')
                elif isinstance(start_urls, (list, tuple)):
                    self.start_urls = list(start_urls)
                else:
                    self.start_urls = search_specific_urls
            else:
                self.start_urls = search_specific_urls
        else:
            # If no search query, use the provided start_urls or default ones
            if start_urls:
                if isinstance(start_urls, str):
                    self.start_urls = start_urls.split(',')
                elif isinstance(start_urls, (list, tuple)):
                    self.start_urls = list(start_urls)
                else:
                    self.start_urls = self.default_start_urls
            else:
                self.start_urls = self.default_start_urls
            
        logger.info(f"Starting URLs: {self.start_urls}")
    
    def parse(self, response):
        # Extract links to follow
        for link in response.css('a::attr(href)').getall():
            if self.should_follow(link):
                yield response.follow(link, self.parse)
        
        # Check if page contains valuable resources
        if self.is_resource_page(response):
            yield self.extract_resource(response)
    
    def should_follow(self, url):
        # Define rules for which URLs to follow
        # Avoid irrelevant pages, focus on content-rich areas
        relevant_patterns = [
            r'tutorial', r'guide', r'doc', r'example', r'resource', 
            r'learn', r'library', r'framework', r'tool', r'cheatsheet'
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
            response.css('article'), response.css('.markdown-body')
        ]
        
        return any(indicator for indicator in resource_indicators)
    
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
        languages = ['python', 'javascript', 'java', 'cpp', 'c++', 'ruby', 'php', 'golang', 'rust', 'zig', 'concurrency', 'async', 'mvcc']
        detected_languages = [lang for lang in languages if lang.lower() in (title + ' ' + description).lower()]
        
        # If search query is provided, verify it's somewhat related to the content
        if self.search_query:
            # Add the search query as a detected language if it's not already included
            # This helps ensure we're finding content related to our search
            if self.search_query.lower() not in [l.lower() for l in detected_languages]:
                detected_languages.append(self.search_query.lower())
            
            # Check if content is related to the search query
            if self.search_query.lower() not in (title + ' ' + description).lower():
                # Check if query appears in the page content
                page_text = ' '.join(response.css('body ::text').getall())
                if self.search_query.lower() not in page_text.lower():
                    # Skip if not related to search query at all
                    return None
        
        # Extract main content based on common content containers
        content_selectors = [
            'article', '.markdown-body', '.post-content',
            '#content', '.content', 'main'
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
        
        logger.info(f"Found resource: {title} ({resource_type})")
        return resource