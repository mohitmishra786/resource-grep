# api/main.py  
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse  
from elasticsearch import Elasticsearch  
from search.index import SearchIndex  
import json  
from crawler.resource_crawler.spiders.resource_spider import ResourceSpider  
from scrapy.crawler import CrawlerRunner  
from twisted.internet import reactor  
import asyncio  
from multiprocessing import Process  
import logging  
from fastapi.middleware.cors import CORSMiddleware  

# Configure logging  
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  

app = FastAPI()  

# Add CORS middleware  
app.add_middleware(  
    CORSMiddleware,  
    allow_origins=["*"],  # In production, replace with your frontend domain  
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)  

# Mount static files  
app.mount("/static", StaticFiles(directory="static"), name="static")  

# Serve index.html at root  
@app.get("/")  
async def read_root():  
    return FileResponse("static/index.html")  

class ConnectionManager:  
    def __init__(self):  
        self.active_connections: list[WebSocket] = []  

    async def connect(self, websocket: WebSocket):  
        await websocket.accept()  
        self.active_connections.append(websocket)  
        logger.info("New WebSocket connection established")  

    def disconnect(self, websocket: WebSocket):  
        self.active_connections.remove(websocket)  
        logger.info("WebSocket connection closed")  

    async def send_message(self, message: str, websocket: WebSocket):  
        await websocket.send_text(message)  

manager = ConnectionManager()  

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

                # Send acknowledgment  
                await websocket.send_json({  
                    "status": "started",  
                    "message": f"Starting search for: {query}"  
                })  

                # Start crawler process  
                def crawler_callback(results):  
                    asyncio.run(websocket.send_json({  
                        "status": "success",  
                        "data": results  
                    }))  

                # Initialize search  
                search_index = SearchIndex()  

                try:  
                    async for results in search_index.search_stream(query):  
                        if results:  
                            await websocket.send_json({  
                                "status": "success",  
                                "data": results,  
                                "finished": False  
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
            except Exception as e:  
                logger.error(f"Error processing message: {str(e)}")  
                await websocket.send_json({  
                    "status": "error",  
                    "message": str(e)  
                })  

    except Exception as e:  
        logger.error(f"WebSocket error: {str(e)}")  
        manager.disconnect(websocket)  

# Health check endpoint  
@app.get("/health")  
async def health_check():  
    return {"status": "healthy"}  