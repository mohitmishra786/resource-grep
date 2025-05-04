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
                # Major programming resource sites
                f'https://github.com/topics/{search_query}',
                f'https://stackoverflow.com/questions/tagged/{search_query}',
                f'https://dev.to/t/{search_query}',
                f'https://medium.com/search?q={search_query}',
                f'https://www.geeksforgeeks.org/search/{search_query}',
                f'https://www.freecodecamp.org/news/search/?query={search_query}',
                f'https://www.digitalocean.com/community/tutorials?q={search_query}',
                f'https://realpython.com/search?q={search_query}',
                f'https://www.tutorialspoint.com/index.htm?search={search_query}',
                f'https://hackernoon.com/search?query={search_query}',
                f'https://substack.com/search?q={search_query}',
                
                # Documentation sites
                f'https://docs.python.org/3/search.html?q={search_query}',
                f'https://developer.mozilla.org/en-US/search?q={search_query}',
                f'https://www.w3schools.com/search/search.php?q={search_query}',
                
                # General search engines
                f'https://www.google.com/search?q={search_query}+programming+tutorial',
                f'https://www.google.com/search?q={search_query}+coding+guide',
                f'https://www.google.com/search?q={search_query}+programming+examples',
                f'https://www.bing.com/search?q={search_query}+programming+guide',
                f'https://duckduckgo.com/?q={search_query}+programming',
                
                # Forums
                f'https://www.reddit.com/search/?q={search_query}+programming',
                f'https://news.ycombinator.com/item?id=search&q={search_query}',
                
                # Video platforms
                f'https://www.youtube.com/results?search_query={search_query}+programming+tutorial',
                
                # University course repositories
                f'https://ocw.mit.edu/search/?q={search_query}',
                f'https://www.coursera.org/search?query={search_query}',
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
        """
        Determine whether to follow a URL during crawling.
        More permissive to allow broader internet searches.
        """
        # Skip non-HTTP links, images, etc.
        if not url or not url.startswith(('http://', 'https://')):
            return False
            
        # Skip file downloads
        file_extensions = ['.pdf', '.zip', '.tar', '.gz', '.rar', '.jpg', '.jpeg', '.png', '.gif', '.svg']
        if any(url.lower().endswith(ext) for ext in file_extensions):
            return False
            
        # Patterns for potentially valuable content
        valuable_patterns = [
            # Programming-related
            r'tutorial', r'guide', r'learn', r'example', r'code', r'sample',
            r'resource', r'document', r'reference', r'cheatsheet', r'lesson',
            r'course', r'class', r'education', r'curriculum', r'bootcamp',
            # Technology areas
            r'api', r'library', r'framework', r'tool', r'development', r'programming',
            r'software', r'developer', r'coding', r'engineer', r'computer',
            # Formats
            r'blog', r'article', r'post', r'forum', r'discussion', r'question', 
            r'answer', r'explanation', r'overview'
        ]
        
        # General programming domains to prioritize
        priority_domains = [
            'github.com', 'stackoverflow.com', 'dev.to', 'medium.com', 
            'freecodecamp.org', 'realpython.com', 'digitalocean.com',
            'tutorialspoint.com', 'w3schools.com', 'mozilla.org', 'youtube.com',
            'reddit.com', 'hackernews.com', 'substack.com', 'docs.google.com'
        ]
        
        # Get the domain
        url_domain = urlparse(url).netloc
        
        # Always follow links from priority domains
        if any(domain in url_domain for domain in priority_domains):
            return True
            
        # Follow links related to the search query if provided
        if self.search_query and self.search_query.lower() in url.lower():
            return True
            
        # Follow URLs that match valuable patterns
        if any(re.search(pattern, url, re.I) for pattern in valuable_patterns):
            return True
            
        # Be more permissive for URLs that might lead to valuable content
        if 'blog' in url_domain or 'docs' in url_domain or 'wiki' in url_domain:
            return True
            
        # Follow more links if we're on a page that is likely resource-related
        # This helps with discovery of new resources
        return False
    
    def is_resource_page(self, response):
        """
        Detect if a page contains valuable programming resources.
        More inclusive to catch a wider variety of content.
        """
        # Check for common programming content indicators
        resource_indicators = [
            # Code examples
            response.css('pre'), response.css('code'), 
            response.css('.highlight'), response.css('.code'),
            
            # Documentation structures
            response.css('.markdown-body'), response.css('.documentation'),
            response.css('.api-docs'), response.css('.reference'),
            
            # Tutorials and guides
            response.xpath('//h1[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "guide")]'),
            response.xpath('//h1[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "tutorial")]'),
            response.xpath('//h1[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "how to")]'),
            
            # Common content containers
            response.css('article'), response.css('.post'), 
            response.css('.entry'), response.css('.content'),
            response.css('#content'), response.css('main'),
            
            # Technical blogs
            response.css('.blog-post'), response.css('.article'),
            
            # Forums and Q&A
            response.css('.question'), response.css('.answer'),
            response.css('.post-text'), response.css('.comment-body'),
            
            # Educational content
            response.css('.lesson'), response.css('.course'),
            response.css('.curriculum'), response.css('.tutorial'),
        ]
        
        # If any indicators are found, this might be a resource page
        if any(indicator for indicator in resource_indicators):
            return True
            
        # Check for keywords in URLs that suggest valuable content
        url = response.url.lower()
        valuable_url_patterns = [
            'tutorial', 'guide', 'learn', 'how-to', 'lesson', 
            'example', 'documentation', 'reference', 'course'
        ]
        if any(pattern in url for pattern in valuable_url_patterns):
            return True
            
        # Check meta tags for relevant keywords
        meta_keywords = response.css('meta[name="keywords"]::attr(content)').get() or ""
        meta_description = response.css('meta[name="description"]::attr(content)').get() or ""
        tech_keywords = ['programming', 'developer', 'code', 'software', 'engineering', 'tutorial', 'api', 'language']
        
        if any(keyword in meta_keywords.lower() for keyword in tech_keywords) or \
           any(keyword in meta_description.lower() for keyword in tech_keywords):
            return True
            
        # Check for presence of the search query in title or headers
        if self.search_query:
            title = response.css('title::text').get() or ""
            h1_text = ' '.join(response.css('h1::text').getall())
            
            if self.search_query.lower() in title.lower() or self.search_query.lower() in h1_text.lower():
                return True
                
        # Default to False if no indicators match
        return False
    
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
        
        # Detect programming language/technology
        languages = [
            # Programming languages
            'python', 'javascript', 'typescript', 'java', 'kotlin', 'c', 'c++', 'c#', 
            'go', 'golang', 'rust', 'swift', 'objective-c', 'ruby', 'php', 'scala', 
            'perl', 'haskell', 'clojure', 'erlang', 'elixir', 'dart', 'r', 'julia',
            'fortran', 'assembly', 'bash', 'shell', 'powershell', 'matlab', 'zig',
            
            # Web technologies
            'html', 'css', 'sass', 'less', 'jquery', 'react', 'vue', 'angular', 
            'svelte', 'ember', 'backbone', 'next.js', 'nuxt.js', 'django', 'flask', 
            'fastapi', 'express', 'spring', 'laravel', 'symfony', 'rails',
            
            # Mobile
            'android', 'ios', 'react native', 'flutter', 'xamarin',
            
            # Databases and storage
            'sql', 'mysql', 'postgresql', 'mongodb', 'sqlite', 'redis', 'cassandra',
            'dynamodb', 'firebase', 'supabase', 'mariadb', 'oracle', 'neo4j', 'graphql',
            
            # Cloud and infrastructure
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'serverless',
            'devops', 'cicd', 'jenkins', 'github actions', 'gitlab ci',
            
            # AI and data science
            'machine learning', 'ai', 'artificial intelligence', 'data science',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            
            # Concepts and paradigms
            'algorithm', 'data structure', 'functional programming', 'oop',
            'concurrency', 'async', 'mvcc', 'microservices', 'rest api', 'websocket',
            'security', 'authentication', 'encryption', 'blockchain', 'web3',
            
            # Tools and productivity
            'git', 'vscode', 'vim', 'emacs', 'intellij', 'eclipse', 'atom',
            'testing', 'debugging', 'performance', 'optimization'
        ]
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