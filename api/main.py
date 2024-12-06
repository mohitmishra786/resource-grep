# api/main.py  
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse  
from elasticsearch import Elasticsearch  
from search.index import SearchIndex  
import json  
import logging  
import redis  
from datetime import datetime  
from fastapi.middleware.cors import CORSMiddleware  
from typing import List, Dict, Any  

# Configure logging  
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  

app = FastAPI()

# Add this to your api/main.py after FastAPI initialization  
# Replace the startup_event function with this:  
@app.on_event("startup")  
async def startup_event():  
    try:  
        # Initialize Elasticsearch  
        es_client = Elasticsearch(['http://localhost:9200'])  

        # Check if index exists  
        if not es_client.indices.exists(index='websearch'):  
            # Create index with mappings  
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
                        "description": {"type": "text"}  
                    }  
                }  
            }  
            es_client.indices.create(index='websearch', body=mappings)  
            logger.info("Created Elasticsearch index 'websearch'")  

        # Add test documents  
        test_docs = [  
            {  
                "url": "http://test.com/flask",  
                "title": "Flask Web Framework",  
                "content": "Flask is a lightweight WSGI web application framework in Python. It is designed to make getting started quick and easy, with the ability to scale up to complex applications.",  
                "description": "Python web framework for building web applications",  
                "domain": "test.com",  
                "resource_type": "framework",  
                "timestamp": datetime.now().isoformat()  
            },  
            {  
                "url": "http://test.com/django",  
                "title": "Django Web Framework",  
                "content": "Django is a high-level Python Web framework that encourages rapid development and clean, pragmatic design.",  
                "description": "Full-featured Python web framework",  
                "domain": "test.com",  
                "resource_type": "framework",  
                "timestamp": datetime.now().isoformat()  
            }  
        ]  

        for doc in test_docs:  
            try:  
                es_client.index(index='websearch', id=doc['url'], body=doc)  
                logger.info(f"Added test document: {doc['title']}")  
            except Exception as e:  
                logger.error(f"Error adding test document: {str(e)}")  

        # Log index status  
        stats = es_client.indices.stats(index='websearch')  
        doc_count = stats['indices']['websearch']['total']['docs']['count']  
        logger.info(f"Elasticsearch index 'websearch' contains {doc_count} documents")  

    except Exception as e:  
        logger.error(f"Elasticsearch initialization error: {str(e)}")  
        raise  

# Initialize services  
try:  
    redis_client = redis.Redis(host='localhost', port=6379, db=0)  
    es_client = Elasticsearch(['http://localhost:9200'])  
    search_index = SearchIndex()  

    # Test connections  
    redis_client.ping()  
    es_client.info()  
    logger.info("Successfully connected to Redis and Elasticsearch")  
except Exception as e:  
    logger.error(f"Failed to initialize services: {str(e)}")  
    raise  

# Add CORS middleware  
app.add_middleware(  
    CORSMiddleware,  
    allow_origins=["*"],  
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)  

# Mount static files  
app.mount("/static", StaticFiles(directory="static"), name="static")  

class ConnectionManager:  
    def __init__(self):  
        self.active_connections: List[WebSocket] = []  
        self.redis_client = redis_client  

    async def connect(self, websocket: WebSocket):  
        try:  
            await websocket.accept()  
            self.active_connections.append(websocket)  
            logger.info("New WebSocket connection established")  
        except Exception as e:  
            logger.error(f"Error accepting WebSocket connection: {str(e)}")  
            raise  

    def disconnect(self, websocket: WebSocket):  
        try:  
            self.active_connections.remove(websocket)  
            logger.info("WebSocket connection closed")  
        except ValueError:  
            pass  

    async def send_message(self, message: str, websocket: WebSocket):  
        try:  
            await websocket.send_text(message)  
        except Exception as e:  
            logger.error(f"Error sending message: {str(e)}")  
            self.disconnect(websocket)  

manager = ConnectionManager()  

@app.get("/")  
async def read_root():  
    return FileResponse("static/index.html")  

# Replace the websocket_endpoint function with this:  
@app.websocket("/ws/search")  
async def websocket_endpoint(websocket: WebSocket):  
    await manager.connect(websocket)  
    try:  
        while True:  
            try:  
                data = await websocket.receive_text()  
                logger.info(f"Received WebSocket data: {data}")  

                search_data = json.loads(data)  
                query = search_data['query']  
                limit = search_data.get('limit')  

                logger.info(f"Processing search query: {query} with limit: {limit}")  

                await websocket.send_json({  
                    "status": "started",  
                    "message": f"Starting search for: {query}"  
                })  

                search_index = SearchIndex()  
                result_count = 0  

                try:  
                    async for results in search_index.search_stream(query):  
                        if results:  
                            result_count += len(results)  
                            await websocket.send_json({  
                                "status": "success",  
                                "data": results,  
                                "finished": False  
                            })  

                    # Send completion message  
                    await websocket.send_json({  
                        "status": "success",  
                        "message": f"Found {result_count} results",  
                        "finished": True  
                    })  

                except Exception as e:  
                    logger.error(f"Search error: {str(e)}")  
                    await websocket.send_json({  
                        "status": "error",  
                        "message": f"Search error: {str(e)}"  
                    })  

            except WebSocketDisconnect:  
                logger.info("WebSocket disconnected")  
                manager.disconnect(websocket)  
                break  
            except Exception as e:  
                logger.error(f"Error processing message: {str(e)}")  
                await websocket.send_json({  
                    "status": "error",  
                    "message": str(e)  
                })  

    except Exception as e:  
        logger.error(f"WebSocket error: {str(e)}")  
        manager.disconnect(websocket)  

@app.get("/health")  
async def health_check():  
    """Health check endpoint with service status"""  
    health_status = {  
        "status": "healthy",  
        "services": {  
            "redis": "connected" if redis_client.ping() else "disconnected",  
            "elasticsearch": "connected" if es_client.ping() else "disconnected"  
        }  
    }  
    return health_status  

# Cleanup on shutdown  
@app.on_event("shutdown")  
async def shutdown_event():  
    """Cleanup connections on shutdown"""  
    try:  
        redis_client.close()  
        es_client.close()  
        logger.info("Cleaned up connections")  
    except Exception as e:  
        logger.error(f"Error during cleanup: {str(e)}")  