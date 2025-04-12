from elasticsearch import Elasticsearch
import json

class ResourceSearch:
    def __init__(self, es_host='elasticsearch', es_port=9200):
        # Updated initialization for newer Elasticsearch client versions
        self.es = Elasticsearch([f'http://{es_host}:{es_port}'])
    
    def instant_search(self, query, filters=None, page=0, size=10):
        """
        Perform an instant search for resources
        
        Args:
            query (str): The search query
            filters (dict): Optional filters (type, language, etc.)
            page (int): Page number (0-based)
            size (int): Results per page
            
        Returns:
            dict: Search results with hits and facets
        """
        # Build the search query
        search_body = {
            "from": page * size,
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^3",
                                    "description^2",
                                    "content",
                                    "code_snippets^2",
                                    "tags^2"
                                ]
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {},
                    "content": {},
                    "code_snippets": {"pre_tags": ["<code>"], "post_tags": ["</code>"]}
                }
            },
            "aggs": {
                "resource_types": {
                    "terms": {"field": "type.keyword"}
                }
            }
        }
        
        # Add filters if provided
        if filters:
            for field, value in filters.items():
                if value:
                    if field == "language":
                        # Handle both language and languages fields
                        language_filter = {
                            "bool": {
                                "should": [
                                    {"term": {"language": value}},
                                    {"term": {"languages": value}}
                                ]
                            }
                        }
                        search_body["query"]["bool"].setdefault("filter", []).append(language_filter)
                    else:
                        filter_clause = {"term": {field: value}}
                        search_body["query"]["bool"].setdefault("filter", []).append(filter_clause)
        
        # Execute search
        results = self.es.search(index="resources", body=search_body)
        
        # Format the results
        formatted_results = {
            "total": results["hits"]["total"]["value"],
            "took": results["took"],
            "hits": [],
            "facets": {
                "resource_types": results["aggregations"]["resource_types"]["buckets"],
                "languages": []  # Empty list since we removed this aggregation
            }
        }
        
        # Keep track of unique languages for facets
        unique_languages = {}
        
        # Format hits
        for hit in results["hits"]["hits"]:
            # Get source data and handle potential field names
            source = hit["_source"]
            language = source.get("language") 
            if language is None and "languages" in source and source["languages"]:
                language = source["languages"][0]  # Use first language if languages list exists
            
            # Add to unique languages for facets if language exists
            if language:
                if language not in unique_languages:
                    unique_languages[language] = 0
                unique_languages[language] += 1
            
            # Set default quality_score if not present
            quality_score = source.get("quality_score", 0.7)
            
            formatted_hit = {
                "id": hit["_id"],
                "score": hit["_score"],
                "url": source["url"],
                "title": source["title"],
                "description": source["description"],
                "type": source["type"],
                "language": language,
                "quality_score": quality_score
            }
            
            # Add highlights if available
            if "highlight" in hit:
                formatted_hit["highlights"] = hit["highlight"]
            
            formatted_results["hits"].append(formatted_hit)
        
        # Convert unique languages to facets format
        for lang, count in unique_languages.items():
            formatted_results["facets"]["languages"].append({
                "key": lang,
                "doc_count": count
            })
        
        return formatted_results