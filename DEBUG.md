# Resource-Grep Debugging Guide

This document provides detailed information on how to debug and monitor each component of the resource-grep system.

## System Overview

The resource-grep system consists of several components:

1. **Elasticsearch** - Stores indexed resources
2. **Redis** - Manages queues and real-time communication
3. **Crawler** - Collects resources from the web
4. **Processor** - Processes and extracts data from crawled resources
5. **API** - Handles search requests and initiates crawls
6. **Streaming API** - Provides real-time search results
7. **Frontend** - Web interface for users

## Checking Component Status

### 1. Elasticsearch

Check if Elasticsearch is running:
```bash
docker compose ps elasticsearch
```

Check indices and document count:
```bash
curl -X GET "http://localhost:9200/_cat/indices?v"
```

Check specific index details:
```bash
curl -X GET "http://localhost:9200/resources/_stats"
```

Count documents in resources index:
```bash
curl -X GET "http://localhost:9200/resources/_count"
```

### 2. Redis

Check if Redis is running:
```bash
docker compose ps redis
```

Check Redis keys:
```bash
docker exec resource-grep-redis-1 redis-cli KEYS "*"
```

Monitor Redis in real-time:
```bash
docker exec resource-grep-redis-1 redis-cli MONITOR
```

Check crawler queues:
```bash
docker exec resource-grep-redis-1 redis-cli LLEN "crawler:pending_urls"
docker exec resource-grep-redis-1 redis-cli SCARD "crawler:seen_urls"
docker exec resource-grep-redis-1 redis-cli SCARD "crawler:visited_urls"
```

### 3. Crawler

Check crawler status:
```bash
docker compose ps crawler
```

View crawler logs:
```bash
docker compose logs crawler
```

Follow crawler logs in real-time:
```bash
docker compose logs -f crawler
```

Manually start a crawler job:
```bash
docker compose exec crawler python run_crawler.py "your search term"
```

### 4. Processor

Check processor status:
```bash
docker compose ps processor
```

View processor logs:
```bash
docker compose logs processor
```

Follow processor logs in real-time:
```bash
docker compose logs -f processor
```

### 5. API

Check API status:
```bash
docker compose ps api
```

Test API search endpoint:
```bash
curl -X GET "http://localhost:8000/search?q=python+tutorial"
```

View API logs:
```bash
docker compose logs api
```

Check system status:
```bash
curl -X GET "http://localhost:8000/status"
```

Manually start crawler from API:
```bash
curl -X POST "http://localhost:8000/crawler/start" -H "Content-Type: application/json" -d '{"urls": []}'
```

### 6. Streaming API

Check streaming API status:
```bash
docker compose ps streaming_api
```

View streaming API logs:
```bash
docker compose logs streaming_api
```

### 7. Frontend

Check frontend status:
```bash
docker compose ps frontend
```

Access the frontend in a browser:
```
http://localhost:3000
```

## Common Issues and Solutions

### No Search Results

If search results aren't appearing:

1. Check if Elasticsearch has documents:
   ```bash
   curl -X GET "http://localhost:9200/resources/_count"
   ```

2. Check if the crawler is running:
   ```bash
   docker compose ps crawler
   ```

3. Check crawler logs for errors:
   ```bash
   docker compose logs crawler
   ```

### Crawler Not Working

If the crawler isn't collecting data:

1. Check crawler logs:
   ```bash
   docker compose logs crawler
   ```

2. Try starting a crawler job manually:
   ```bash
   docker compose exec crawler python run_crawler.py "test query"
   ```

3. Check Redis for pending URLs:
   ```bash
   docker exec resource-grep-redis-1 redis-cli LLEN "crawler:pending_urls"
   ```

### WebSocket Connection Issues

If the WebSocket isn't connecting:

1. Check if streaming API is running:
   ```bash
   docker compose ps streaming_api
   ```

2. Check streaming API logs:
   ```bash
   docker compose logs streaming_api
   ```

3. Try accessing the WebSocket endpoint directly (requires wscat tool):
   ```bash
   wscat -c ws://localhost:8001/ws/search?query=python
   ```

### Restart Components

To restart specific components:

```bash
docker compose restart [component_name]
```

For example:
```bash
docker compose restart crawler
```

To restart the entire system:
```bash
docker compose down
docker compose up -d
```

## Monitoring the System

### View Live Processing

To see the full process from crawling to indexing:

1. Open the web UI at http://localhost:3000
2. Enter a search term that hasn't been indexed (e.g., "react hooks")
3. Switch to WebSocket mode using the toggle buttons
4. Open the developer console (F12) to see detailed logs
5. Check the "Processing Status" panel that appears when activities are happening

### Monitor Redis

For a real-time view of what's happening in Redis:

```bash
docker exec resource-grep-redis-1 redis-cli MONITOR
```

### Monitor Logs

For a complete view of all logs:

```bash
docker compose logs -f
```

Or follow specific components:

```bash
docker compose logs -f api crawler processor
```

## Rebuilding Components

If you make changes to a component:

```bash
docker compose build [component_name]
docker compose up -d [component_name]
```

For example:
```bash
docker compose build streaming_api
docker compose up -d streaming_api
``` 

<!-- Just for local reference -->
```bash
curl -X GET "http://localhost:8000/search?q=cobol" | jq && sleep 30 && curl -X GET "http://localhost:8000/search?q=cobol" | jq
```