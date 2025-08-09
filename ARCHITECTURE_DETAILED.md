# Resource Grep Detailed Architecture

This document provides a comprehensive overview of the Resource Grep system architecture, including component interactions, dependencies, and API endpoints.

## System Overview

Resource Grep is a real-time search engine for programming resources that instantly finds relevant developer resources like tutorials, documentation, code snippets, and articles from across the entire internet. The system follows a microservices architecture with event-driven processing for scalability and real-time updates.

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

## Core Components

### 1. Web Interface (Frontend)
- **Technology**: HTML/CSS/JavaScript (vanilla) with Tailwind CSS
- **Purpose**: Provides the user interface for searching resources
- **Features**:
  - Instant search with real-time updates
  - Resource filtering and sorting
  - WebSocket-based real-time results with HTTP fallback
  - Resource display with syntax highlighting for code snippets
  - Responsive design for multiple devices

### 2. API Gateway (API Service)
- **Technology**: FastAPI (Python)
- **Purpose**: Serves as the entry point for all client HTTP requests
- **Features**:
  - RESTful API for search queries
  - Request validation and basic rate limiting
  - Crawler job initiation
  - System status reporting

### 3. Streaming API (WebSocket Service)
- **Technology**: FastAPI (Python) with WebSocket support
- **Purpose**: Provides real-time search results via WebSockets
- **Features**:
  - Real-time search result streaming
  - Status and progress updates
  - Multi-client broadcasting
  - Connection management with reconnection logic

### 4. Search Engine
- **Technology**: Elasticsearch
- **Purpose**: Provides search functionality across indexed resources
- **Features**:
  - Full-text search with highlighting
  - Faceted search (by language, resource type, etc.)
  - Relevance scoring based on content quality
  - Custom mappings for code-specific search

### 5. Resource Crawler
- **Technology**: Scrapy (Python)
- **Purpose**: Discovers and extracts programming resources from the web
- **Features**:
  - Distributed crawling with multiple worker support
  - Search engine integration for seed URLs
  - Resource extraction with heuristic detection
  - Content extraction including code snippets
  - Quality scoring for discovered resources

### 6. Coordinator Service
- **Technology**: Python with Redis
- **Purpose**: Manages distributed crawl jobs and worker coordination
- **Features**:
  - Worker management and monitoring
  - Job distribution and load balancing
  - URL queue management
  - System statistics reporting

### 7. Resource Processor
- **Technology**: Python
- **Purpose**: Processes and enriches crawled resources
- **Features**:
  - Content cleaning and normalization
  - Resource type classification
  - Code snippet extraction and language detection
  - Quality scoring based on multiple heuristics
  - Duplicate detection

### 8. Job Queue and Messaging
- **Technology**: Redis
- **Purpose**: Manages crawl jobs and message passing between services
- **Features**:
  - Priority-based crawl job scheduling
  - Distributed message passing
  - Pub/Sub for real-time updates
  - Job status tracking

## Key Dependencies and Their Interactions

### 1. FastAPI (API & Streaming Services)
- **Purpose**: Web framework for both HTTP and WebSocket services
- **Interactions**:
  - Communicates with Elasticsearch for search queries
  - Interacts with Redis for real-time messaging
  - Triggers crawler jobs via subprocess calls

### 2. Elasticsearch
- **Purpose**: Search engine and primary data store
- **Interactions**:
  - Receives indexing requests from crawlers
  - Processes search queries from API services
  - Provides search results with relevance scoring

### 3. Redis
- **Purpose**: In-memory data structure store for messaging and queuing
- **Interactions**:
  - Manages job queues for crawler coordination
  - Enables real-time messaging between services
  - Tracks crawler progress and status

### 4. Scrapy
- **Purpose**: Web crawling framework
- **Interactions**:
  - Crawls web resources based on search queries
  - Extracts content and metadata from web pages
  - Sends processed resources to Elasticsearch for indexing

### 5. Nginx
- **Purpose**: Web server for serving static frontend files
- **Interactions**:
  - Serves HTML/CSS/JS files to clients
  - Proxies API requests to backend services

## Data Flow

### Search Flow
1. User enters a search query in the web interface
2. Query is sent to the API Gateway via HTTP or WebSocket
3. API Gateway forwards the query to Elasticsearch
4. Elasticsearch returns matching resources
5. If few results are found, a new crawl job is initiated
6. Results are returned to the user via HTTP or streamed via WebSocket
7. New resources are streamed to the user as they're discovered and indexed

### Crawling Flow
1. Crawl job is created by the API Gateway
2. Coordinator service schedules the job and distributes to crawler workers
3. Resource Crawler begins crawling based on search query
4. Extracted resources are sent to the Resource Processor
5. Resource Processor enriches and validates the resources
6. Processed resources are indexed in Elasticsearch
7. Streaming Service is notified of new resources
8. New resources are streamed to connected WebSocket clients

## API Endpoints

### HTTP API (Port: 8000)

#### GET `/search`
Search for programming resources with optional filters.

**Query Parameters:**
- `q` (string, required): Search query (e.g., "python tutorial")
- `type` (string, optional): Filter by resource type (e.g., "tutorial", "documentation")
- `language` (string, optional): Filter by programming language
- `page` (integer, optional): Page number (default: 0)
- `size` (integer, optional): Results per page (default: 10, max: 50)

**Response:**
```json
{
  "took": 45,
  "total": 128,
  "hits": [...],
  "facets": {
    "resource_types": [...],
    "languages": [...]
  }
}
```

#### POST `/crawler/start`
Start a new crawler job with optional seed URLs.

**Request Body:**
```json
{
  "urls": ["https://example.com"]
}
```

**Response:**
```json
{
  "status": "started",
  "job_id": "uuid-string"
}
```

#### GET `/status`
Get system status and basic statistics.

**Response:**
```json
{
  "indexed_resources": 15483,
  "index_size": 13428745694,
  "status": "operational"
}
```

### WebSocket API (Port: 8001)

#### WebSocket `/ws/search`
Connect for real-time search results.

**Query Parameters:**
- `query` (string, required): Search query
- `filters` (string, optional): JSON-encoded filters

**Message Types:**
1. **Stats**: Search statistics
2. **Result**: Individual search result
3. **Status**: General status message
4. **Crawling**: Crawling progress updates
5. **Processing**: Resource processing updates
6. **Indexing**: Indexing progress updates
7. **Error**: Error messages

## Authentication Methods

Currently, Resource Grep does not implement authentication for its public API endpoints. All endpoints are publicly accessible. Future implementations could include:

1. **API Key Authentication**: For rate limit increases and access to premium features
2. **OAuth 2.0**: For user account integration
3. **JWT Tokens**: For session management in advanced features

## Scalability Considerations

1. **API Gateway**: Can be scaled horizontally behind a load balancer
2. **Search Service**: Elasticsearch cluster can add nodes for increased search capacity
3. **Resource Crawler**: Multiple crawler instances can run in parallel
4. **Coordinator Service**: Can manage multiple crawler clusters
5. **Resource Processor**: Stateless design allows for easy scaling
6. **Job Queue**: Redis can be configured as a cluster for high availability
7. **Streaming Service**: Can be scaled horizontally with sticky sessions

## Security Considerations

1. **API Security**:
   - Rate limiting to prevent abuse
   - Input validation to prevent injection attacks
   - CORS configuration for browser security

2. **Crawler Security**:
   - User-agent identification
   - Respect for robots.txt (configurable)
   - Rate limiting per domain
   - TLS/SSL for secure connections

3. **Data Security**:
   - Sanitization of indexed content
   - No storage of sensitive information
   - Regular security scanning of indexed content

4. **Infrastructure Security**:
   - Network isolation between components
   - Least privilege principles for service accounts
   - Regular security updates