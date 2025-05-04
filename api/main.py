from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import time
import requests
from requests.exceptions import ConnectionError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append('/app')

# Wait for Elasticsearch to be ready
def wait_for_elasticsearch(host='elasticsearch', port=9200, max_retries=30, delay=2):
    """Wait for Elasticsearch to become available"""
    url = f"http://{host}:{port}"
    logger.info(f"Waiting for Elasticsearch at {url}")
    
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"Elasticsearch is ready at {url}")
                return True
        except ConnectionError:
            pass
        
        logger.info(f"Elasticsearch not ready yet. Retrying in {delay} seconds... ({i+1}/{max_retries})")
        time.sleep(delay)
    
    logger.error(f"Could not connect to Elasticsearch after {max_retries} attempts")
    return False

# Wait for Elasticsearch before importing modules that depend on it
es_host = os.environ.get('ELASTICSEARCH_HOST', 'elasticsearch')
es_port = int(os.environ.get('ELASTICSEARCH_PORT', 9200))
wait_for_elasticsearch(es_host, es_port)

# Now import modules that depend on Elasticsearch
from search.index import ResourceSearch
from crawler.run_crawler import start_crawler

# Request models
class CrawlerStartRequest(BaseModel):
    urls: list[str] = []

app = FastAPI(title="Resource Grep API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

search_engine = ResourceSearch(es_host=es_host, es_port=es_port)

@app.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    type: str = Query(None, description="Filter by resource type"),
    language: str = Query(None, description="Filter by programming language"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    size: int = Query(10, ge=1, le=50, description="Results per page")
):
    """
    Search for resources with instant results
    """
    filters = {}
    if type:
        filters["type"] = type
    if language:
        filters["language"] = language
        
    try:
        results = search_engine.instant_search(q, filters, page, size)
        
        # If no results are found, trigger a crawler job
        if results["total"] == 0 and page == 0:
            logger.info(f"No results found for '{q}'. Starting a crawler job.")
            job_id = start_crawler(seed_urls=None, search_query=q)
            
            # Add a note to the results indicating crawling has started
            results["crawling_started"] = True
            results["job_id"] = job_id
            results["message"] = "No existing results found. Started crawling the web for this query."
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawler/start")
async def start_crawling(request: CrawlerStartRequest):
    """
    Start the crawler with optional seed URLs
    """
    try:
        job_id = start_crawler(request.urls)
        return {"status": "started", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """
    Get system status
    """
    try:
        # Get basic stats from Elasticsearch
        stats = search_engine.es.indices.stats(index="resources")
        return {
            "indexed_resources": stats["indices"]["resources"]["total"]["docs"]["count"],
            "index_size": stats["indices"]["resources"]["total"]["store"]["size_in_bytes"],
            "status": "operational"
        }
    except Exception as e:
        return {
            "indexed_resources": 0,
            "index_size": 0,
            "status": "initializing",
            "message": str(e)
        }