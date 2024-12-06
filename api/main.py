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

@app.websocket("/ws/search")  
async def websocket_endpoint(websocket: WebSocket):  
    await manager.connect(websocket)  

    try:  
        while True:  
            try:  
                # Receive the search query  
                data = await websocket.receive_text()  
                search_data = json.loads(data)  
                query = search_data['query']  
                limit = search_data.get('limit')  

                logger.info(f"Received search query: {query} with limit: {limit}")  

                # Store search query in Redis  
                redis_client.lpush("recent_searches", json.dumps({  
                    "query": query,  
                    "timestamp": datetime.now().isoformat(),  
                    "limit": limit  
                }))  

                # Send acknowledgment  
                await websocket.send_json({  
                    "status": "started",  
                    "message": f"Starting search for: {query}"  
                })  

                # Perform search  
                try:  
                    result_count = 0  
                    async for results in search_index.search_stream(query):  
                        if results:  
                            result_count += len(results)  
                            await websocket.send_json({  
                                "status": "success",  
                                "data": results,  
                                "finished": False  
                            })  

                            if limit and result_count >= int(limit):  
                                break  

                    # Send completion message  
                    await websocket.send_json({  
                        "status": "success",  
                        "message": "Search completed",  
                        "finished": True  
                    })  

                except Exception as e:  
                    logger.error(f"Search error: {str(e)}")  
                    await websocket.send_json({  
                        "status": "error",  
                        "message": f"Search error: {str(e)}"  
                    })  

            except WebSocketDisconnect:  
                manager.disconnect(websocket)  
                break  
            except json.JSONDecodeError as e:  
                logger.error(f"Invalid JSON received: {str(e)}")  
                await websocket.send_json({  
                    "status": "error",  
                    "message": "Invalid search query format"  
                })  
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