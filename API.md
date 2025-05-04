# Resource Grep API Reference

This document provides complete details on the Resource Grep API endpoints, request/response formats, and usage examples.

## API Overview

Resource Grep offers two primary interfaces:
- **RESTful HTTP API**: For standard search queries and crawler management
- **WebSocket API**: For real-time search results and status updates

## Base URLs

- **HTTP API**: `http://<host>:8000`
- **WebSocket API**: `ws://<host>:8001`

## REST API Endpoints

### Search Resources

Retrieves programming resources matching a query.

```
GET /search
```

#### Query Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| q         | string | Yes      | Search query (e.g., "python tutorial") |
| type      | string | No       | Filter by resource type (e.g., "tutorial", "documentation", "article", "repository") |
| language  | string | No       | Filter by programming language |
| page      | integer| No       | Page number (default: 0) |
| size      | integer| No       | Results per page (default: 10, max: 100) |

#### Response Format

```json
{
  "took": 45,
  "total": 128,
  "page": 0,
  "size": 10,
  "hits": [
    {
      "_id": "abc123",
      "_score": 0.87,
      "_source": {
        "url": "https://example.com/resource",
        "title": "Python Tutorial",
        "description": "Learn Python programming from scratch",
        "content": "Python is a high-level programming language...",
        "code_snippets": ["print('Hello World')"],
        "tags": "python,programming,tutorial",
        "domain": "example.com",
        "type": "tutorial",
        "languages": ["python"],
        "timestamp": "2023-05-15T14:22:31.894Z",
        "quality_score": 0.85
      },
      "highlight": {
        "content": ["Python is a <em>high-level</em> programming language..."],
        "code_snippets": ["<em>print</em>('Hello World')"]
      }
    }
  ],
  "aggregations": {
    "resource_types": {
      "buckets": [
        {"key": "tutorial", "doc_count": 45},
        {"key": "documentation", "doc_count": 32},
        {"key": "article", "doc_count": 28},
        {"key": "repository", "doc_count": 23}
      ]
    },
    "languages": {
      "buckets": [
        {"key": "python", "doc_count": 87},
        {"key": "javascript", "doc_count": 24},
        {"key": "java", "doc_count": 17}
      ]
    }
  }
}
```

### Start Crawler

Manually initiate a crawler job for a specific search query.

```
POST /crawl
```

#### Request Body

```json
{
  "query": "cobol tutorial",
  "depth": 3,
  "priority": "high"
}
```

#### Parameters

| Parameter | Type    | Required | Description |
|-----------|---------|----------|-------------|
| query     | string  | Yes      | Search query to crawl for |
| depth     | integer | No       | Crawling depth (default: 2, max: 5) |
| priority  | string  | No       | Job priority: "low", "medium", "high" (default: "medium") |

#### Response

```json
{
  "job_id": "crawler-job-123456",
  "status": "started",
  "estimated_time": "5m",
  "message": "Crawler job started for query 'cobol tutorial'"
}
```

### Get Crawler Status

Get the status of a crawler job.

```
GET /crawl/status/{job_id}
```

#### Response

```json
{
  "job_id": "crawler-job-123456",
  "status": "running",
  "progress": 0.45,
  "pages_crawled": 127,
  "resources_found": 34,
  "started_at": "2023-05-15T14:22:31.894Z",
  "estimated_completion": "2023-05-15T14:27:31.894Z"
}
```

### Get Index Stats

Get statistics about the search index.

```
GET /stats
```

#### Response

```json
{
  "total_resources": 15483,
  "languages": [
    {"name": "python", "count": 3254},
    {"name": "javascript", "count": 2876},
    {"name": "java", "count": 1854}
  ],
  "resource_types": [
    {"name": "tutorial", "count": 5431},
    {"name": "documentation", "count": 4327},
    {"name": "article", "count": 3892},
    {"name": "repository", "count": 1833}
  ],
  "domains": [
    {"name": "github.com", "count": 2453},
    {"name": "stackoverflow.com", "count": 1874},
    {"name": "medium.com", "count": 954}
  ],
  "index_size_bytes": 13428745694,
  "last_updated": "2023-05-15T14:22:31.894Z"
}
```

## WebSocket API

### Real-time Search

Connect to the WebSocket endpoint for real-time search results.

```
ws://<host>:8001/ws/search?query={query}&filters={filters_json}
```

#### Query Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| query     | string | Yes      | Search query |
| filters   | string | No       | JSON-encoded filters |

Example filters format:
```json
{
  "type": "tutorial",
  "language": "python"
}
```

#### Message Types

The WebSocket connection streams different message types:

1. **Stats Message**
```json
{
  "type": "stats",
  "data": {
    "total": 128,
    "took": 45
  }
}
```

2. **Result Message**
```json
{
  "type": "result",
  "data": {
    "id": "abc123",
    "url": "https://example.com/resource",
    "title": "Python Tutorial",
    "description": "Learn Python programming from scratch",
    "type": "tutorial",
    "language": "python",
    "score": 0.87,
    "quality_score": 0.85,
    "highlight": {
      "content": ["Python is a <em>high-level</em> programming language..."],
      "code_snippets": ["<em>print</em>('Hello World')"]
    },
    "source": "realtime"
  }
}
```

3. **Status Message**
```json
{
  "type": "status",
  "data": {
    "message": "Searching for new resources..."
  }
}
```

4. **Crawling Message**
```json
{
  "type": "crawling",
  "data": {
    "message": "Started crawling for 'python tutorial'",
    "job_id": "crawler-job-123456"
  }
}
```

5. **Processing Message**
```json
{
  "type": "processing",
  "data": {
    "message": "Processing page: https://example.com/python-tutorial"
  }
}
```

6. **Indexing Message**
```json
{
  "type": "indexing",
  "data": {
    "message": "Indexed 5 new resources"
  }
}
```

7. **Error Message**
```json
{
  "type": "error",
  "data": {
    "message": "Failed to process search",
    "code": "search_error"
  }
}
```

### WebSocket Connection Handling

- The connection remains open for real-time updates
- The client will receive messages as new results are found
- The server may send status updates periodically
- Clients should implement reconnection logic with exponential backoff

## Error Codes and Handling

| Error Code       | HTTP Status | Description |
|------------------|-------------|-------------|
| `invalid_query`  | 400         | The search query is invalid or empty |
| `search_error`   | 500         | An error occurred during search processing |
| `crawler_error`  | 500         | Failed to start or manage crawler job |
| `not_found`      | 404         | Resource or job not found |
| `auth_error`     | 401         | Authentication error (for protected endpoints) |

## Rate Limiting

- **Public API**: 60 requests per minute
- **Authenticated API**: 300 requests per minute
- **Crawler Initiation**: 5 requests per hour (public), 20 per hour (authenticated)

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1620243628
```

## Client Libraries

Official client libraries:
- [Python Client](https://github.com/resource-grep/resource-grep-python)
- [JavaScript Client](https://github.com/resource-grep/resource-grep-js)

## Examples

### cURL Examples

#### Basic Search
```bash
curl -X GET "http://localhost:8000/search?q=python%20tutorial"
```

#### Filtered Search
```bash
curl -X GET "http://localhost:8000/search?q=python%20tutorial&type=tutorial&language=python"
```

#### Start Crawler
```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"query": "fortran tutorial", "depth": 3}'
```

### JavaScript WebSocket Example

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/search?query=python%20tutorial');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'result':
      console.log('New result:', message.data.title);
      // Add result to UI
      break;
    case 'status':
      console.log('Status update:', message.data.message);
      // Update status in UI
      break;
    // Handle other message types
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Implement fallback to HTTP API
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
  // Implement reconnection logic
};
``` 