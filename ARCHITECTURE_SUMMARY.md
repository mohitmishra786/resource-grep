# Resource Grep Architecture Summary

## Main Pieces of the System's Architecture

Resource Grep consists of eight core components working together in a microservices architecture:

1. **Web Interface (Frontend)** - Static HTML/JS/CSS served by Nginx
2. **API Gateway** - FastAPI service handling HTTP requests
3. **Streaming API** - WebSocket server for real-time updates
4. **Search Engine** - Elasticsearch for indexing and searching
5. **Resource Crawler** - Scrapy-based web crawler
6. **Coordinator Service** - Manages distributed crawling jobs
7. **Resource Processor** - Processes and enriches crawled content
8. **Job Queue/Messaging** - Redis for queuing and real-time communication

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    Load Balancer                                    │
└┬─────────────────────────────────────┬──────────────────────────────────────────────┬┘
 │                                     │                                              │
┌▼──────────────┐        ┌─────────────▼──────────────┐             ┌─────────────────▼────────┐
│   API Server  │        │   Streaming API Server     │             │    Frontend Server         │
│ (Port: 8000)  │        │    (Port: 8001)            │             │     (Port: 3000)           │
└┬──────────────┘        └┬────────────────────────────┘             └┬─────────────────────────┘
 │                        │                                           │
 │ Search Requests        │ WebSocket Connections                     │ Static Files
 │                        │                                           │
┌▼────────────────────────▼───────────────────────────────────────────▼─────────────────────────┐
│                                      Redis (Messaging)                                      │
│                                    (Port: 6379)                                              │
└┬─────────────────────────────────────────────────────────────────────────────────────────────┬┘
 │                                                                                             │
 │ Job Queue/Coordination                                                                     │ Pub/Sub for Real-time Updates
 │                                                                                             │
┌▼─────────────────────────────────────────────────────────────────────────────────────────────▼┐
│                                   Elasticsearch (Search Engine)                             │
│                                     (Port: 9200)                                              │
└┬─────────────────────────────────────────────────────────────────────────────────────────────┬┘
 │                                                                                             │
 │ Search Queries                                                                             │ Indexing
 │                                                                                             │
┌▼─────────────────────────────────────────────────────────────────────────────────────────────▼┐
│                                         Coordinator Service                                   │
│                                                                                               │
│  Distributes crawling jobs to multiple crawler workers                                        │
└┬─────────────────────────────────────────────────────────────────────────────────────────────┬┘
 │                                                                                             │
 │ Job Distribution                                                                           │ Status Updates
 │                                                                                             │
┌▼─────────────────────────────────────────────────────────────────────────────────────────────▼┐
│                                          Crawler Service                                      │
│                                                                                               │
│  Multiple crawler workers that discover and extract programming resources from the web        │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Dependencies and How They Interact

### Core Dependencies:

1. **FastAPI** - Python web framework for API and WebSocket services
2. **Elasticsearch** - Search engine and data storage
3. **Redis** - In-memory data store for messaging and queuing
4. **Scrapy** - Python web crawling framework
5. **Nginx** - Web server for static file serving

### Interaction Flow:

1. **User Request Flow**:
   - Frontend makes HTTP requests to API Gateway (port 8000)
   - API Gateway queries Elasticsearch for search results
   - For real-time updates, frontend connects to Streaming API (port 8001)
   - Streaming API subscribes to Redis for live updates

2. **Crawling Flow**:
   - API Gateway triggers crawler jobs via subprocess
   - Coordinator Service manages job distribution using Redis queues
   - Crawler workers (Scrapy) extract content from the web
   - Processed resources are indexed in Elasticsearch
   - New resources are published to Redis for real-time updates

3. **Data Storage**:
   - Elasticsearch stores all indexed resources
   - Redis manages job queues and real-time messaging
   - File system stores raw crawled content and logs

## API Endpoints and Authentication Methods

### HTTP API Endpoints (Port: 8000):

1. **GET `/search`**
   - **Purpose**: Search for programming resources
   - **Parameters**: 
     - `q` (string, required): Search query
     - `type` (string, optional): Filter by resource type
     - `language` (string, optional): Filter by programming language
     - `page` (int, optional): Page number (default: 0)
     - `size` (int, optional): Results per page (default: 10, max: 50)
   - **Authentication**: None (public endpoint)

2. **POST `/crawler/start`**
   - **Purpose**: Start a new crawler job
   - **Body**: JSON with `urls` array (optional)
   - **Authentication**: None (public endpoint)

3. **GET `/status`**
   - **Purpose**: Get system status and statistics
   - **Authentication**: None (public endpoint)

### WebSocket API Endpoints (Port: 8001):

1. **WebSocket `/ws/search`**
   - **Purpose**: Real-time search results and updates
   - **Parameters**:
     - `query` (string, required): Search query
     - `filters` (string, optional): JSON-encoded filters
   - **Authentication**: None (public endpoint)
   - **Message Types**: stats, result, status, crawling, processing, indexing, error

### Authentication Methods:

Currently, Resource Grep does not implement authentication for any of its endpoints. All APIs are publicly accessible. This design choice prioritizes ease of use and accessibility but may require authentication implementation for production deployments to prevent abuse.

Potential future authentication methods could include:
1. **API Key Authentication** - For rate limit increases
2. **OAuth 2.0** - For user account integration
3. **JWT Tokens** - For session management in advanced features

### Rate Limiting:

While not explicitly implemented in the current codebase, the documentation suggests:
- Public API: 60 requests per minute
- Authenticated API: 300 requests per minute (future feature)
- Crawler initiation: 5 requests per hour (public), 20 per hour (authenticated) (future feature)