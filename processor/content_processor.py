import re
import json
import hashlib
from datetime import datetime
from elasticsearch import Elasticsearch

class ContentProcessor:
    def __init__(self, es_host='elasticsearch', es_port=9200):
        # Updated initialization for newer Elasticsearch client versions
        self.es = Elasticsearch([f'http://{es_host}:{es_port}'])
        self._ensure_index()
    
    def _ensure_index(self):
        """Create the Elasticsearch index if it doesn't exist"""
        if not self.es.indices.exists(index='resources'):
            self.es.indices.create(
                index='resources',
                body={
                    "settings": {
                        "analysis": {
                            "analyzer": {
                                "code_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase"]
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "url": {"type": "keyword"},
                            "title": {"type": "text"},
                            "description": {"type": "text"},
                            "content": {"type": "text"},
                            "code_snippets": {
                                "type": "text",
                                "analyzer": "code_analyzer"
                            },
                            "tags": {"type": "keyword"},
                            "type": {"type": "keyword"},
                            "language": {"type": "keyword"},
                            "quality_score": {"type": "float"},
                            "indexed_date": {"type": "date"}
                        }
                    }
                }
            )
    
    def process_resource(self, resource):
        """Process and enrich a resource before indexing"""
        # Generate unique ID for deduplication
        resource_id = hashlib.md5(resource['url'].encode()).hexdigest()
        
        # Clean content
        if 'content' in resource:
            resource['content'] = self._clean_text(resource['content'])
        
        # Detect programming language
        resource['language'] = self._detect_language(resource)
        
        # Calculate quality score
        resource['quality_score'] = self._calculate_quality(resource)
        
        # Add timestamp
        resource['indexed_date'] = datetime.now().isoformat()
        
        # Index the resource
        self.es.index(index='resources', id=resource_id, body=resource)
        
        return resource_id
    
    def _clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
    def _detect_language(self, resource):
        """Detect the programming language of the resource"""
        # Simple language detection based on keywords and URL
        languages = {
            'python': ['python', 'django', 'flask', 'numpy', 'pandas'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
            'java': ['java', 'spring', 'maven', 'gradle'],
            'go': ['golang', 'go '],
            'rust': ['rust', 'cargo'],
            'php': ['php', 'laravel', 'symfony'],
            'ruby': ['ruby', 'rails'],
            'c#': ['c#', 'csharp', '.net', 'dotnet'],
            'c++': ['c++', 'cpp']
        }
        
        # Check URL, title, and content
        text_to_check = ' '.join([
            resource.get('url', ''),
            resource.get('title', ''),
            resource.get('description', ''),
            ' '.join(resource.get('tags', '').split(',') if resource.get('tags') else [])
        ]).lower()
        
        for lang, keywords in languages.items():
            if any(kw in text_to_check for kw in keywords):
                return lang
        
        # Check code snippets for language indicators
        for snippet in resource.get('code_snippets', []):
            for lang, keywords in languages.items():
                if any(kw in snippet.lower() for kw in keywords):
                    return lang
        
        return 'unknown'
    
    def _calculate_quality(self, resource):
        """Calculate a quality score for the resource"""
        score = 0
        
        # Score based on content length
        if 'content' in resource and resource['content']:
            content_length = len(resource['content'])
            if content_length > 5000:
                score += 3
            elif content_length > 1000:
                score += 2
            elif content_length > 500:
                score += 1
        
        # Score based on code snippets
        if 'code_snippets' in resource and resource['code_snippets']:
            score += min(len(resource['code_snippets']), 3)
        
        # Score based on description quality
        if 'description' in resource and resource['description']:
            if len(resource['description']) > 100:
                score += 2
            elif len(resource['description']) > 50:
                score += 1
        
        # Score based on source reputation (simple example)
        reputation_sites = ['github.com', 'stackoverflow.com', 'docs.python.org']
        if any(site in resource.get('url', '') for site in reputation_sites):
            score += 3
        
        return min(score / 10, 1.0)  # Normalize to 0-1