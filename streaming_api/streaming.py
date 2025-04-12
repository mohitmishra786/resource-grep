from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
import redis
import json
import asyncio
import logging
import uuid
from elasticsearch import AsyncElasticsearch
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resource Grep Streaming API")

# Redis pubsub connection pool
redis_pool = None
# Elasticsearch connection
es_client = None

class StreamingSearchManager:
    def __init__(self):
        self.active_connections = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_result(self, client_id: str, result: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(result)

# Create manager
manager = StreamingSearchManager()

@app.on_event("startup")
async def startup_event():
    global redis_pool, es_client
    
    # Connect to Redis
    redis_host = os.environ.get('REDIS_HOST', 'redis')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port)
    
    # Connect to Elasticsearch
    es_host = os.environ.get('ELASTICSEARCH_HOST', 'elasticsearch')
    es_port = int(os.environ.get('ELASTICSEARCH_PORT', 9200))
    es_client = AsyncElasticsearch([f"http://{es_host}:{es_port}"])

@app.websocket("/ws/search")
async def websocket_search(
    websocket: WebSocket, 
    query: str = Query(...),
    filters: str = Query(None)
):
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    # Parse filters if any
    filter_dict = json.loads(filters) if filters else {}
    
    # Start Redis pubsub listener
    redis_client = redis.Redis(connection_pool=redis_pool)
    pubsub = redis_client.pubsub()
    
    # Subscribe to realtime results from crawler
    search_channel = f"search:results:{query}"
    pubsub.subscribe(search_channel)
    
    # Track seen results to avoid duplicates
    seen_urls = set()
    
    # Task to perform initial search
    initial_search_task = None
    
    try:
        # Start initial search in Elasticsearch
        initial_search_task = asyncio.create_task(
            search_elasticsearch(query, filter_dict, client_id, seen_urls)
        )
        
        # Listen for real-time results from crawler
        while True:
            message = pubsub.get_message(timeout=0.1)
            if message and message['type'] == 'message':
                # Process real-time result from Redis
                result = json.loads(message['data'])
                
                # Skip if URL already seen
                if result['url'] in seen_urls:
                    continue
                
                # Add to seen URLs
                seen_urls.add(result['url'])
                
                # Apply filters if needed
                if filter_and_format_result(result, filter_dict):
                    # Send to client
                    await manager.send_result(client_id, {
                        'type': 'result',
                        'data': result,
                        'source': 'realtime'
                    })
            
            # Check if client is still connected
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        # Cleanup
        manager.disconnect(client_id)
        pubsub.unsubscribe()
        if initial_search_task and not initial_search_task.done():
            initial_search_task.cancel()

async def search_elasticsearch(query, filters, client_id, seen_urls):
    """Perform search in Elasticsearch and stream results"""
    try:
        # Build the search query
        search_body = {
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
        results = await es_client.search(
            index="resources", 
            body=search_body,
            size=100
        )
        
        # Send total count first
        total_hits = results["hits"]["total"]["value"]
        await manager.send_result(client_id, {
            'type': 'stats',
            'data': {
                'total': total_hits,
                'took': results["took"]
            }
        })
        
        # Send each result
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            url = source["url"]
            
            # Skip if already seen
            if url in seen_urls:
                continue
            
            # Add to seen URLs
            seen_urls.add(url)
            
            # Format result
            result = {
                'id': hit["_id"],
                'score': hit["_score"],
                'url': url,
                'title': source["title"],
                'description': source["description"],
                'type': source["type"],
                'source': 'elasticsearch'
            }
            
            # Handle language field
            if "language" in source:
                result["language"] = source["language"]
            elif "languages" in source and source["languages"]:
                result["language"] = source["languages"][0]
            
            # Send to client
            await manager.send_result(client_id, {
                'type': 'result',
                'data': result
            })
            
            # Small delay to avoid overwhelming the client
            await asyncio.sleep(0.01)
        
        # Signal end of initial results
        await manager.send_result(client_id, {
            'type': 'status',
            'data': {
                'message': 'Initial search complete, streaming real-time results'
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching Elasticsearch: {e}")
        await manager.send_result(client_id, {
            'type': 'error',
            'data': {
                'message': f"Search error: {str(e)}"
            }
        })

def filter_and_format_result(result, filters):
    """Apply filters to a real-time result and format it"""
    # Apply language filter
    if 'language' in filters and filters['language']:
        result_lang = result.get('language', '').lower()
        if result_lang != filters['language'].lower():
            return False
    
    # Apply type filter
    if 'type' in filters and filters['type']:
        result_type = result.get('type', '').lower()
        if result_type != filters['type'].lower():
            return False
    
    return True

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("streaming:app", host="0.0.0.0", port=8001, reload=True) 