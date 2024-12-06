# search/index.py  
from elasticsearch import Elasticsearch  
from typing import Dict, List, Generator  
import asyncio  

class SearchIndex:  
    def __init__(self):  
        self.es = Elasticsearch(['http://localhost:9200'])  

    async def search_stream(self, query: str) -> Generator[Dict, None, None]:  
        """Stream search results as they come"""  

        # Initial search  
        results = self.es.search(  
            index='websearch',  
            body={  
                'query': {  
                    'multi_match': {  
                        'query': query,  
                        'fields': ['title^3', 'content^2', 'code_snippets^4'],  
                        'type': 'best_fields'  
                    }  
                },  
                'highlight': {  
                    'fields': {  
                        'content': {},  
                        'code_snippets': {}  
                    }  
                }  
            },  
            scroll='2m'  
        )  

        # Yield initial results  
        yield results['hits']['hits']  

        # Continue scrolling  
        scroll_id = results['_scroll_id']  
        while True:  
            results = self.es.scroll(scroll_id=scroll_id, scroll='2m')  
            if not results['hits']['hits']:  
                break  
            yield results['hits']['hits']  