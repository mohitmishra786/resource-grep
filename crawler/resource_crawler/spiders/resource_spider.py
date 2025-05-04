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
        # Legacy programming languages
        'https://www.tutorialspoint.com/cobol/index.htm',
        'https://www.mainframestechhelp.com/tutorials/cobol/',
        'https://www.ibm.com/docs/en/cobol-zos',
        'https://www.tutorialspoint.com/fortran/index.htm',
        'https://fortran-lang.org/learn/',
        'https://github.com/topics/fortran',
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
                f'https://stackoverflow.com/search?q={search_query}',
                f'https://dev.to/t/{search_query}',
                f'https://dev.to/search?q={search_query}',
                f'https://medium.com/search?q={search_query}',
                f'https://www.geeksforgeeks.org/search/{search_query}',
                f'https://www.freecodecamp.org/news/search/?query={search_query}',
                f'https://www.digitalocean.com/community/tutorials?q={search_query}',
                f'https://realpython.com/search?q={search_query}',
                f'https://www.tutorialspoint.com/index.htm?search={search_query}',
                f'https://www.tutorialspoint.com/{search_query}/index.htm',
                f'https://hackernoon.com/search?query={search_query}',
                f'https://substack.com/search?q={search_query}',
                
                # Documentation sites
                f'https://docs.python.org/3/search.html?q={search_query}',
                f'https://developer.mozilla.org/en-US/search?q={search_query}',
                f'https://www.w3schools.com/search/search.php?q={search_query}',
                f'https://ibm.github.io/mainframe-downloads/search.html?q={search_query}',
                f'https://docs.oracle.com/search/?q={search_query}',
                f'https://learn.microsoft.com/en-us/search/?terms={search_query}',
                f'https://www.ibm.com/search?q={search_query}',
                
                # General search engines - increased coverage
                f'https://www.google.com/search?q={search_query}+programming+tutorial',
                f'https://www.google.com/search?q={search_query}+programming+guide',
                f'https://www.google.com/search?q={search_query}+coding+tutorial',
                f'https://www.google.com/search?q={search_query}+programming+examples',
                f'https://www.google.com/search?q={search_query}+language+tutorial',
                f'https://www.google.com/search?q={search_query}+programming+book',
                f'https://www.google.com/search?q={search_query}+documentation',
                f'https://www.bing.com/search?q={search_query}+programming+guide',
                f'https://duckduckgo.com/?q={search_query}+programming',
                f'https://search.brave.com/search?q={search_query}+programming',
                
                # Forums
                f'https://www.reddit.com/search/?q={search_query}+programming',
                f'https://www.reddit.com/r/learnprogramming/search/?q={search_query}',
                f'https://www.reddit.com/r/programming/search/?q={search_query}',
                f'https://news.ycombinator.com/item?id=search&q={search_query}',
                f'https://forums.oracle.com/ords/apexds/domain/dev-community/search?search={search_query}',
                f'https://community.ibm.com/community/user/search?query={search_query}',
                
                # Video platforms
                f'https://www.youtube.com/results?search_query={search_query}+programming+tutorial',
                
                # University course repositories
                f'https://ocw.mit.edu/search/?q={search_query}',
                f'https://www.coursera.org/search?query={search_query}',
                f'https://www.khanacademy.org/search?page_search_query={search_query}',
                f'https://www.edx.org/search?q={search_query}',
                
                # Specialized programming sites
                f'https://legacy.cplusplus.com/search.do?q={search_query}',
                f'https://en.cppreference.com/mwiki/index.php?title=Special%3ASearch&search={search_query}',
                f'https://www.sourcecodesworld.com/source/search.asp?key={search_query}',
                f'https://sourceforge.net/directory/?q={search_query}',
                f'https://mvnrepository.com/search?q={search_query}',
                
                # Legacy language specific resources
                f'https://www.microfocus.com/search?q={search_query}',
                f'https://www.mainframestechhelp.com/search-results?query={search_query}',
                f'https://www.ibm.com/search?lang=en&cc=us&q={search_query}',
                f'https://fortran-lang.org/search/?q={search_query}',
                f'https://www.ibm.com/docs/en/search/{search_query}',
                f'https://www.tutorialspoint.com/{search_query.lower()}/index.htm',
                
                # Academic resources
                f'https://scholar.google.com/scholar?q={search_query}+programming',
                f'https://arxiv.org/search/?query={search_query}&searchtype=all',
                f'https://dl.acm.org/action/doSearch?AllField={search_query}',
                
                # Books and documentation
                f'https://books.google.com/books?q={search_query}+programming',
                f'https://archive.org/search?query={search_query}%20programming',
                f'https://www.pdfdrive.com/search?q={search_query}+programming',
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
        Extremely permissive to allow comprehensive internet searches.
        """
        # Skip non-HTTP links, images, etc.
        if not url or not url.startswith(('http://', 'https://')):
            return False
            
        # Skip resource-intensive file downloads
        file_extensions = ['.zip', '.tar', '.gz', '.rar', '.exe', '.dmg', '.iso']
        if any(url.lower().endswith(ext) for ext in file_extensions):
            return False
        
        # Always follow URLs with search query term
        if self.search_query and self.search_query.lower() in url.lower():
            return True
        
        # Priority domains to always follow - expanded significantly
        priority_domains = [
            # General programming sites
            'github.com', 'stackoverflow.com', 'dev.to', 'medium.com', 
            'freecodecamp.org', 'realpython.com', 'digitalocean.com',
            'tutorialspoint.com', 'w3schools.com', 'mozilla.org', 'youtube.com',
            'reddit.com', 'hackernews.com', 'substack.com', 'docs.google.com',
            'kubernetes.io', 'docker.com', 'python.org', 'reactjs.org',
            'angular.io', 'vuejs.org', 'rust-lang.org', 'golang.org',
            'developer.mozilla.org', 'aws.amazon.com', 'cloud.google.com',
            'docs.microsoft.com', 'graphql.org', 'postgresql.org', 'mysql.com',
            
            # Legacy language resources
            'ibm.com', 'mainframestechhelp.com', 'microfocus.com', 'borland.com',
            'fortran-lang.org', 'cobol.com', 'mainframegurukul.com', 'cobolforgcc.com',
            'clarabridge.com', 'netcobol.com', 'ibm.github.io', 'legacy.cplusplus.com',
            'sourcecodesworld.com', 'findbestopensource.com', 'alternet.cobol.com',
            'opencobol.org', 'fujitsu.com', 'visualcobol.net', 'jics.macc.wisc.edu',
            'fortranplus.co.uk', 'netlib.org', 'fortran.com', 'gfortran.com',
            'j3-fortran.org', 'gcc.gnu.org', 'cse.yorku.ca',
            
            # Academic resources
            'scholar.google.com', 'arxiv.org', 'dl.acm.org', 'ieeexplore.ieee.org',
            'academia.edu', 'researchgate.net', 'mit.edu', 'stanford.edu',
            'berkeley.edu', 'cam.ac.uk', 'ox.ac.uk', 'harvard.edu', 'princeton.edu',
            
            # Documentation and references
            'devdocs.io', 'readthedocs.io', 'docs.oracle.com', 'wikiwand.com',
            'cppreference.com', 'manual.com', 'docs.rs', 'dartdocs.org',
            'apidock.com', 'jsdoc.app', 'kotlinlang.org', 'scaladoc.org',
            
            # Books and learning resources
            'oreilly.com', 'manning.com', 'packtpub.com', 'informit.com',
            'apress.com', 'wiley.com', 'springer.com', 'pragprog.com',
            'edx.org', 'coursera.org', 'udemy.com', 'pluralsight.com',
            'khanacademy.org', 'codecademy.com', 'udacity.com',
            
            # Additional forums and community sites
            'hashnode.com', 'lobste.rs', 'slashdot.org', 'infoq.com',
            'codingforums.com', 'quora.com', 'sitepoint.com', 'dzone.com'
        ]
        
        # Get the domain
        url_domain = urlparse(url).netloc
        
        # Always follow links from priority domains
        if any(domain in url_domain for domain in priority_domains):
            return True
            
        # Follow URLs with programming-related paths
        programming_paths = [
            'developer', 'programming', 'tutorial', 'guide', 'learn', 
            'course', 'documentation', 'reference', 'manual', 'handbook',
            'example', 'sample', 'snippet', 'howto', 'language', 'framework',
            'library', 'package', 'module', 'function', 'class', 'method',
            'interface', 'api', 'sdk', 'code', 'development', 'software',
            'engineering', 'computer-science', 'tech', 'algorithm', 'cobol',
            'fortran', 'mainframe', 'legacy', 'vintage-computing'
        ]
        
        if any(path in url.lower() for path in programming_paths):
            return True
        
        # Filter out obviously irrelevant content - very limited list now
        irrelevant_patterns = [
            r'checkout', r'payment', r'unsubscribe'
        ]
        
        if any(re.search(pattern, url, re.I) for pattern in irrelevant_patterns):
            return False
            
        # Follow most URLs by default to drastically expand crawling breadth
        # This is an aggressive approach to ensure we don't miss content
        return True
    
    def is_resource_page(self, response):
        """
        Detect if a page contains valuable programming resources.
        Highly inclusive to catch a wide variety of content, especially for legacy languages.
        """
        # If this is a search query for legacy languages, be more permissive
        if self.search_query and self.search_query.lower() in ['cobol', 'fortran', 'pascal', 'basic', 'ada', 'lisp', 'prolog', 'smalltalk', 'mainframe']:
            # For legacy languages, almost any page that mentions the language is valuable
            page_text = ' '.join(response.css('body ::text').getall()).lower()
            if self.search_query.lower() in page_text:
                # If the search term appears multiple times, it's likely a relevant resource
                if page_text.count(self.search_query.lower()) >= 2:
                    return True
        
        # Check for common programming content indicators
        resource_indicators = [
            # Code examples
            response.css('pre'), response.css('code'), 
            response.css('.highlight'), response.css('.code'),
            response.css('.CodeMirror'), response.css('.ace_editor'),
            response.css('.program'), response.css('.syntax'),
            
            # Documentation structures
            response.css('.markdown-body'), response.css('.documentation'),
            response.css('.api-docs'), response.css('.reference'),
            response.css('.man-page'), response.css('.docstring'),
            response.css('.manual'), response.css('.handbook'),
            
            # Tutorials and guides
            response.xpath('//h1[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "guide")]'),
            response.xpath('//h1[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "tutorial")]'),
            response.xpath('//h1[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "how to")]'),
            response.xpath('//h2[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "tutorial")]'),
            response.xpath('//h2[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "guide")]'),
            response.xpath('//h2[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "introduction")]'),
            
            # Legacy language specific indicators
            response.xpath('//pre[contains(@class, "cobol")]'),
            response.xpath('//pre[contains(@class, "fortran")]'),
            response.xpath('//code[contains(@class, "cobol")]'),
            response.xpath('//code[contains(@class, "fortran")]'),
            response.xpath('//table[contains(@class, "syntax")]'),
            response.xpath('//div[contains(@class, "compiler")]'),
            
            # Common content containers
            response.css('article'), response.css('.post'), 
            response.css('.entry'), response.css('.content'),
            response.css('#content'), response.css('main'),
            response.css('.page'), response.css('.doc'),
            
            # Technical blogs
            response.css('.blog-post'), response.css('.article'),
            response.css('.entry-content'), response.css('.blog-entry'),
            
            # Forums and Q&A
            response.css('.question'), response.css('.answer'),
            response.css('.post-text'), response.css('.comment-body'),
            response.css('.reply'), response.css('.discussion'),
            
            # Educational content
            response.css('.lesson'), response.css('.course'),
            response.css('.curriculum'), response.css('.tutorial'),
            response.css('.lecture'), response.css('.module'),
        ]
        
        # If any indicators are found, this might be a resource page
        if any(indicator for indicator in resource_indicators):
            return True
            
        # Check for keywords in URLs that suggest valuable content
        url = response.url.lower()
        valuable_url_patterns = [
            'tutorial', 'guide', 'learn', 'how-to', 'lesson', 
            'example', 'documentation', 'reference', 'course',
            'manual', 'handbook', 'getting-started', 'intro',
            'cheatsheet', 'cookbook', 'primer', 'samples',
            'snippets', 'library', 'framework', 'language',
            'spec', 'standard', 'book', 'ebook', 'workshop',
            'specification', 'resources', 'cheat-sheet',
            'cobol', 'fortran', 'mainframe', 'compiler',
            'interpreter', 'coding', 'programming', 'developer'
        ]
        if any(pattern in url for pattern in valuable_url_patterns):
            return True
            
        # Check meta tags for relevant keywords
        meta_keywords = response.css('meta[name="keywords"]::attr(content)').get() or ""
        meta_description = response.css('meta[name="description"]::attr(content)').get() or ""
        
        # Expanded list of tech keywords to include legacy languages
        tech_keywords = [
            'programming', 'developer', 'code', 'software', 'engineering', 
            'tutorial', 'api', 'language', 'compiler', 'interpreter',
            'mainframe', 'legacy', 'vintage', 'retro', 'historic',
            'cobol', 'fortran', 'algol', 'pascal', 'basic',
            'assembler', 'assembly', 'pl/i', 'pl1', 'ada', 'lisp',
            'prolog', 'smalltalk', 'jcl', 'rpg', 'rexx', 'natural', 
            'ibm', 'mvs', 'z/os', 'os/390', 'vm', 'vse', 'cics',
            'ims', 'db2', 'vsam', 'qsam', 'algorithm', 'data structure'
        ]
        
        if any(keyword in meta_keywords.lower() for keyword in tech_keywords) or \
           any(keyword in meta_description.lower() for keyword in tech_keywords):
            return True
            
        # Check for presence of the search query in title or headers
        if self.search_query:
            title = response.css('title::text').get() or ""
            h1_text = ' '.join(response.css('h1::text').getall())
            h2_text = ' '.join(response.css('h2::text').getall())
            
            if self.search_query.lower() in title.lower() or \
               self.search_query.lower() in h1_text.lower() or \
               self.search_query.lower() in h2_text.lower():
                return True
        
        # For legacy languages, check if there's a significant amount of content
        # with specific legacy language terms
        if self.search_query and self.search_query.lower() in ['cobol', 'fortran', 'pascal', 'basic', 'ada']:
            page_text = ' '.join(response.css('body ::text').getall()).lower()
            
            # Legacy language specific terms
            legacy_terms = {
                'cobol': ['cobol', 'copybook', 'picture', 'identification division', 'data division', 'procedure division', 'compute', 'perform', 'display'],
                'fortran': ['fortran', 'subroutine', 'program', 'implicit', 'real', 'integer', 'dimension', 'format', 'common', 'equivalence'],
                'pascal': ['pascal', 'begin', 'end', 'procedure', 'function', 'var', 'const', 'type', 'program', 'unit'],
                'basic': ['basic', 'gosub', 'goto', 'print', 'input', 'let', 'rem', 'dim', 'data', 'read'],
                'ada': ['ada', 'package', 'procedure', 'function', 'begin', 'end', 'type', 'task', 'protected', 'generic']
            }
            
            # If the language is one we know, check for specific terms
            if self.search_query.lower() in legacy_terms:
                matches = sum(1 for term in legacy_terms[self.search_query.lower()] if term in page_text)
                if matches >= 3:  # If at least 3 specific terms appear, likely a relevant page
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
            'cobol', 'pascal', 'ada', 'lisp', 'prolog', 'smalltalk', 'basic',
            'algol', 'pl/i', 'pl1', 'jcl', 'rpg', 'rexx', 'natural', 'abap',
            'delphi', 'vb', 'visual basic', 'vba', 'actionscript', 'groovy',
            
            # Web technologies
            'html', 'css', 'sass', 'less', 'jquery', 'react', 'vue', 'angular', 
            'svelte', 'ember', 'backbone', 'next.js', 'nuxt.js', 'django', 'flask', 
            'fastapi', 'express', 'spring', 'laravel', 'symfony', 'rails',
            
            # Mobile
            'android', 'ios', 'react native', 'flutter', 'xamarin',
            
            # Databases and storage
            'sql', 'mysql', 'postgresql', 'mongodb', 'sqlite', 'redis', 'cassandra',
            'dynamodb', 'firebase', 'supabase', 'mariadb', 'oracle', 'neo4j', 'graphql',
            'db2', 'vsam', 'ims', 'adabas', 'idms', 'datacom',
            
            # Cloud and infrastructure
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'serverless',
            'devops', 'cicd', 'jenkins', 'github actions', 'gitlab ci',
            'mainframe', 'z/os', 'os/390', 'vm', 'vse', 'tso', 'ispf', 'cics',
            
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
        
        # For legacy languages, improve detection
        page_text = ' '.join(response.css('body ::text').getall()).lower()
        
        # If no languages detected yet, check page content
        if not detected_languages:
            detected_languages = [lang for lang in languages if lang.lower() in page_text]
            
        # Special handling for search query match
        if self.search_query:
            # For legacy languages, prioritize search query
            if self.search_query.lower() in ['cobol', 'fortran', 'pascal', 'basic', 'ada', 'pl/i', 'rpg', 'jcl']:
                detected_languages = [self.search_query.lower()] + [l for l in detected_languages if l.lower() != self.search_query.lower()]
            
            # Add the search query as a detected language if it's not already included
            # This helps ensure we're finding content related to our search
            if self.search_query.lower() not in [l.lower() for l in detected_languages]:
                detected_languages.append(self.search_query.lower())
            
            # For legacy languages, special check for content relevance
            if self.search_query.lower() in ['cobol', 'fortran', 'ada', 'pascal', 'basic', 'pl/i', 'rpg', 'jcl']:
                # Any page that mentions these languages multiple times is likely relevant
                mentions = page_text.count(self.search_query.lower())
                if mentions >= 3:
                    # Skip the general content relevance check for legacy languages
                    pass
                elif self.search_query.lower() not in (title + ' ' + description).lower():
                    # For non-legacy languages, check that content is related
                    if self.search_query.lower() not in page_text:
                        # Skip if not related to search query at all
                        return None
            # Normal content relevance check for modern languages
            elif self.search_query.lower() not in (title + ' ' + description).lower():
                if self.search_query.lower() not in page_text:
                    # Skip if not related to search query at all
                    return None
        
        # Extract main content based on common content containers
        content_selectors = [
            'article', '.markdown-body', '.post-content',
            '#content', '.content', 'main', '.entry-content',
            '.post', '.resource-content', '.documentation',
            '.tutorial', '.lesson', '.guide'
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
        
        # Also check for pre tags without code for legacy languages
        if not code_snippets and self.search_query and self.search_query.lower() in ['cobol', 'fortran', 'pascal', 'basic', 'ada']:
            for pre_block in response.css('pre::text').getall():
                # Only include if it contains the language name or specific keywords
                if self.search_query.lower() in pre_block.lower():
                    code_snippets.append(pre_block)
        
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
        elif 'reference' in title.lower() or 'manual' in title.lower():
            resource_type = 'documentation'
        elif '/github.com/' in response.url:
            resource_type = 'repository'
        elif any(doc in response.url for doc in ['docs', 'documentation', 'reference']):
            resource_type = 'documentation'
        elif any(tut in response.url for tut in ['tutorial', 'guide', 'how-to']):
            resource_type = 'tutorial'
        
        # Calculate quality score based on multiple factors
        quality_score = 0.5  # Start with a baseline score
        
        # Boost for priority domains
        priority_domains = [
            'github.com', 'stackoverflow.com', 'tutorialspoint.com', 
            'ibm.com', 'w3schools.com', 'mozilla.org',
            'docs.oracle.com', 'fortran-lang.org', 'mainframestechhelp.com'
        ]
        if any(pd in domain for pd in priority_domains):
            quality_score += 0.2
            
        # Boost for legacy language sites specific to the search query
        if self.search_query:
            query_priority_domains = {
                'cobol': ['ibm.com', 'microfocus.com', 'tutorialspoint.com/cobol', 'mainframestechhelp.com'],
                'fortran': ['fortran-lang.org', 'gcc.gnu.org', 'netlib.org', 'tutorialspoint.com/fortran'],
                'pascal': ['freepascal.org', 'delphi.org', 'tutorialspoint.com/pascal'],
                'basic': ['visual-basic.com', 'vb6.us', 'vbtutor.net'],
                'ada': ['adaic.org', 'adacore.com', 'getadanow.com']
            }
            
            if self.search_query.lower() in query_priority_domains:
                if any(pd in domain for pd in query_priority_domains[self.search_query.lower()]):
                    quality_score += 0.3
        
        # Boost for code snippets and content length
        if code_snippets:
            quality_score += min(0.2, len(code_snippets) * 0.05)  # Up to 0.2 for code snippets
            
        # Content length boosts quality (comprehensive resources)
        if content:
            content_length = len(content)
            if content_length > 5000:  # Long, detailed content
                quality_score += 0.15
            elif content_length > 2000:  # Medium length content
                quality_score += 0.1
                
        # Cap the quality score at 1.0
        quality_score = min(1.0, quality_score)
        
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
        
        logger.info(f"Found resource: {title} ({resource_type}) - Quality: {quality_score:.2f}")
        return resource