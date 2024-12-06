# search/index.py  
from elasticsearch import Elasticsearch  
from typing import Dict, List, Generator, Any  
import logging  
import asyncio  
from datetime import datetime  

logger = logging.getLogger(__name__)  

class SearchIndex:  
    def __init__(self):  
        self.es = Elasticsearch(['http://localhost:9200'])  
        self._ensure_index()  

    def _ensure_index(self):  
        """Ensure the search index exists with proper mappings"""  
        index_name = 'websearch'  

        if not self.es.indices.exists(index=index_name):  
            mappings = {  
                "mappings": {  
                    "properties": {  
                        "url": {"type": "keyword"},  
                        "title": {"type": "text"},  
                        "content": {"type": "text"},  
                        "code_snippets": {"type": "text"},  
                        "domain": {"type": "keyword"},  
                        "resource_type": {"type": "keyword"},  
                        "timestamp": {"type": "date"},  
                        "keywords": {"type": "keyword"},  
                        "description": {"type": "text"}  
                    }  
                },  
                "settings": {  
                    "number_of_shards": 1,  
                    "number_of_replicas": 0  
                }  
            }  

            try:  
                self.es.indices.create(index=index_name, body=mappings)  
                logger.info(f"Created index '{index_name}' with mappings")  
            except Exception as e:  
                logger.error(f"Error creating index: {str(e)}")  
                raise  

    # search/index.py  
    # Replace the search_stream method with this:  
    async def search_stream(self, query: str) -> Generator[List[Dict], None, None]:  
        try:  
            if not self.es.ping():  
                raise Exception("Elasticsearch is not available")  

            logger.info(f"Performing Elasticsearch search for query: {query}")  

            results = self.es.search(  
                index='websearch',  
                body={  
                    'query': {  
                        'multi_match': {  
                            'query': query,  
                            'fields': ['title^3', 'content^2', 'code_snippets^4', 'description^2'],  
                            'type': 'best_fields',  
                            'fuzziness': 'AUTO'  
                        }  
                    },  
                    'highlight': {  
                        'fields': {  
                            'content': {},  
                            'code_snippets': {},  
                            'description': {}  
                        }  
                    },  
                    'size': 10  
                }  
            )  

            # Process results before yielding  
            processed_results = []  
            for hit in results['hits']['hits']:  
                processed_result = {  
                    'url': hit['_source'].get('url', ''),  
                    'title': hit['_source'].get('title', 'Untitled'),  
                    'description': hit['_source'].get('description', ''),  
                    'domain': hit['_source'].get('domain', ''),  
                    'resource_type': hit['_source'].get('resource_type', 'unknown'),  
                    'snippet': hit.get('highlight', {}).get('content', [''])[0] if 'highlight' in hit else '',  
                    'score': hit['_score']  
                }  
                processed_results.append(processed_result)  

            logger.info(f"Found {len(processed_results)} results")  
            yield processed_results  

        except Exception as e:  
            logger.error(f"Elasticsearch search error: {str(e)}")  
            raise  
    def _process_results(self, results: Dict) -> List[Dict]:  
        """Process and format search results"""  
        processed = []  

        for hit in results['hits']['hits']:  
            source = hit['_source']  
            highlight = hit.get('highlight', {})  

            processed.append({  
                'url': source['url'],  
                'title': source['title'],  
                'domain': source['domain'],  
                'resource_type': source.get('resource_type', 'unknown'),  
                'description': highlight.get('description', [source.get('description', '')])[0],  
                'snippet': highlight.get('content', [''])[0] if 'content' in highlight else '',  
                'code_snippet': highlight.get('code_snippets', [''])[0] if 'code_snippets' in highlight else '',  
                'score': hit['_score'],  
                'timestamp': source.get('timestamp', datetime.now().isoformat())  
            })  

        return processed  

    async def index_document(self, document: Dict):  
        """Index a single document"""  
        try:  
            response = self.es.index(  
                index='websearch',  
                body=document,  
                id=document['url']  
            )  
            logger.info(f"Indexed document: {document['url']}")  
            return response  
        except Exception as e:  
            logger.error(f"Error indexing document: {str(e)}")  
            raise  