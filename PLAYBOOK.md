# Resource Grep Operations Playbook

This playbook provides a comprehensive set of commands and procedures for operating, monitoring, and troubleshooting Resource Grep.

## Table of Contents
- [System Startup](#system-startup)
- [API Operations](#api-operations)
- [Elasticsearch Operations](#elasticsearch-operations)
- [Redis Operations](#redis-operations)
- [Crawler Operations](#crawler-operations)
- [WebSocket Operations](#websocket-operations)
- [Monitoring Operations](#monitoring-operations)
- [Data Inspection](#data-inspection)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)

## System Startup

### Start the Complete System

```bash
# Navigate to the project directory
cd resource-grep

# Start all services using Docker Compose
docker-compose up -d

# Check if all services are running
docker-compose ps
```

Expected output:
```
      Name                    Command               State           Ports
----------------------------------------------------------------------------------
resource-grep_api_1         uvicorn api.main:app --host ...   Up      0.0.0.0:8000->8000/tcp
resource-grep_crawler_1     python -m scrapy crawl resou ...   Up
resource-grep_elasticsearch_1   /usr/local/bin/docker-entr ...   Up      0.0.0.0:9200->9200/tcp, 0.0.0.0:9300->9300/tcp
resource-grep_redis_1       docker-entrypoint.sh redis ...    Up      0.0.0.0:6379->6379/tcp
resource-grep_streaming_1   uvicorn streaming.main:app  ...   Up      0.0.0.0:8001->8001/tcp
resource-grep_web_1         /docker-entrypoint.sh ngin ...    Up      0.0.0.0:80->80/tcp
```

### Start Individual Services

```bash
# Start only Elasticsearch and Redis
docker-compose up -d elasticsearch redis

# Start the API service
docker-compose up -d api

# Start the streaming service
docker-compose up -d streaming

# Start the crawler
docker-compose up -d crawler
```

## API Operations

### Test the API Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "elasticsearch": "connected",
    "redis": "connected"
  }
}
```

### Basic Search Query

```bash
curl -X GET "http://localhost:8000/search?q=python+tutorial"
```

Sample output:
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
        "type": "tutorial",
        "languages": ["python"],
        "quality_score": 0.85
      }
    }
  ]
}
```

### Filtered Search Query

```bash
curl -X GET "http://localhost:8000/search?q=python&type=tutorial&language=python"
```

### Get API Stats

```bash
curl -X GET "http://localhost:8000/stats"
```

### Start a New Crawler Job

```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cobol tutorial",
    "depth": 3,
    "priority": "high"
  }'
```

Expected output:
```json
{
  "job_id": "crawler-job-123456",
  "status": "started",
  "estimated_time": "5m",
  "message": "Crawler job started for query 'cobol tutorial'"
}
```

### Check Crawler Job Status

```bash
curl -X GET "http://localhost:8000/crawl/status/crawler-job-123456"
```

## Elasticsearch Operations

### Check Elasticsearch Cluster Health

```bash
curl -X GET "http://localhost:9200/_cluster/health?pretty"
```

Expected output:
```json
{
  "cluster_name": "docker-cluster",
  "status": "green",
  "timed_out": false,
  "number_of_nodes": 1,
  "number_of_data_nodes": 1,
  "active_primary_shards": 7,
  "active_shards": 7,
  "relocating_shards": 0,
  "initializing_shards": 0,
  "unassigned_shards": 0,
  "delayed_unassigned_shards": 0,
  "number_of_pending_tasks": 0,
  "number_of_in_flight_fetch": 0,
  "task_max_waiting_in_queue_millis": 0,
  "active_shards_percent_as_number": 100.0
}
```

### List All Indices

```bash
curl -X GET "http://localhost:9200/_cat/indices?v"
```

Expected output:
```
health status index         uuid                   pri rep docs.count docs.deleted store.size pri.store.size
green  open   resources-v1  AbCdEfGhIjKlMnOpQrStUv   1   0       1250            0      1.2mb          1.2mb
green  open   crawler-jobs  VwXyZaBcDeFgHiJkLmNoPq   1   0         15            2    125.5kb        125.5kb
```

### Get Index Mappings

```bash
curl -X GET "http://localhost:9200/resources-v1/_mapping?pretty"
```

### Search All Resources

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match_all": {}
    },
    "size": 10
  }'
```

### Count Resources by Type

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "resource_types": {
        "terms": {
          "field": "type",
          "size": 10
        }
      }
    }
  }'
```

### Count Resources by Language

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "languages": {
        "terms": {
          "field": "languages",
          "size": 20
        }
      }
    }
  }'
```

### Get Index Stats

```bash
curl -X GET "http://localhost:9200/resources-v1/_stats?pretty"
```

### Get Disk Usage

```bash
curl -X GET "http://localhost:9200/_cat/allocation?v"
```

## Redis Operations

### Check Redis Info

```bash
docker-compose exec redis redis-cli info
```

### View Active Keys

```bash
docker-compose exec redis redis-cli keys "*"
```

Expected output:
```
1) "crawler:jobs"
2) "crawler:urls:seen"
3) "search:recent_queries"
```

### Count Pending Crawler Jobs

```bash
docker-compose exec redis redis-cli llen "crawler:jobs"
```

### View Crawler Queue

```bash
docker-compose exec redis redis-cli lrange "crawler:jobs" 0 -1
```

### Monitor Real-time Redis Commands

```bash
docker-compose exec redis redis-cli monitor
```

### View Redis Memory Usage

```bash
docker-compose exec redis redis-cli info memory
```

## Crawler Operations

### Manually Run the Crawler

```bash
docker-compose exec crawler python -m scrapy crawl resource_spider -a query="python tutorial"
```

### View Crawler Logs

```bash
docker-compose logs -f crawler
```

### Check Crawler Settings

```bash
docker-compose exec crawler python -c "from resource_crawler.settings import *; print('\n'.join([f'{k}={v}' for k, v in locals().items() if not k.startswith('_')]))"
```

### Test URL Parsing

```bash
docker-compose exec crawler python -c "from resource_crawler.spiders.resource_spider import ResourceSpider; print(ResourceSpider().extract_search_urls('python tutorial'))"
```

### Test Resource Detection

```bash
docker-compose exec crawler python -c "from resource_crawler.pipelines import ResourceDetectionPipeline; pipeline = ResourceDetectionPipeline(); print(pipeline.is_programming_resource({'url': 'https://example.com', 'content': 'Python is a programming language for data science and machine learning. Example: print(\"Hello World\")'}))"
```

## WebSocket Operations

### Test WebSocket Connection

Using websocat (install with `brew install websocat` or `cargo install websocat`):

```bash
websocat ws://localhost:8001/ws/search?query=python
```

Expected output (streaming):
```json
{"type":"status","data":{"message":"Connected. Searching for 'python'..."}}
{"type":"stats","data":{"total":128,"took":45}}
{"type":"result","data":{"id":"abc123","url":"https://example.com/python-tutorial","title":"Python Tutorial"}}
{"type":"result","data":{"id":"def456","url":"https://example.com/python-basics","title":"Python Basics"}}
```

### Monitor WebSocket Server Logs

```bash
docker-compose logs -f streaming
```

## Monitoring Operations

### View All Container Logs

```bash
docker-compose logs -f
```

### Check Container Resource Usage

```bash
docker stats
```

### Check API Request Rate

```bash
# Install ApacheBench if needed
ab -n 100 -c 10 http://localhost:8000/search?q=python
```

### Check API Response Times

```bash
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/search?q=python
```

### Check Service Health

```bash
# API service
curl http://localhost:8000/health

# WebSocket service
curl http://localhost:8001/health

# Elasticsearch
curl http://localhost:9200/_cluster/health

# Redis
docker-compose exec redis redis-cli ping
```

## Data Inspection

### Inspect Total Document Count

```bash
curl -X GET "http://localhost:9200/_cat/count/resources-v1?v"
```

### Get Index Size

```bash
curl -X GET "http://localhost:9200/_cat/indices/resources-v1?v&h=index,store.size"
```

### Inspect Most Recent Documents

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"match_all": {}},
    "size": 10,
    "sort": [{"timestamp": {"order": "desc"}}]
  }'
```

### Inspect Document by ID

```bash
curl -X GET "http://localhost:9200/resources-v1/_doc/abc123?pretty"
```

### Get Top Domains in the Index

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "domains": {
        "terms": {
          "field": "domain",
          "size": 20
        }
      }
    }
  }'
```

### Dump a Sample of Documents

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"match_all": {}},
    "size": 100,
    "sort": [{"_score": {"order": "desc"}}]
  }' > sample_documents.json
```

## Troubleshooting

### Check API Errors

```bash
docker-compose logs -f api | grep ERROR
```

### Check Crawler Errors

```bash
docker-compose logs -f crawler | grep ERROR
```

### Check Elasticsearch Errors

```bash
docker-compose logs -f elasticsearch | grep ERROR
```

### Check Redis Connectivity

```bash
docker-compose exec api python -c "import redis; r = redis.Redis(host='redis', port=6379); print(r.ping())"
```

### Verify Elasticsearch Index Exists

```bash
curl -X HEAD -i "http://localhost:9200/resources-v1"
```

Expected output if index exists:
```
HTTP/1.1 200 OK
```

### Test Search with Explain

```bash
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "explain": true,
    "query": {
      "match": {
        "content": "python tutorial"
      }
    },
    "size": 1
  }'
```

### Reset Crawler State

```bash
# Clear Redis crawler queues
docker-compose exec redis redis-cli del "crawler:jobs" "crawler:urls:seen"

# Restart crawler
docker-compose restart crawler
```

## Performance Tuning

### Increase Elasticsearch Memory

Edit `docker-compose.yml` to allocate more memory to Elasticsearch:

```yaml
elasticsearch:
  environment:
    - ES_JAVA_OPTS=-Xms2g -Xmx2g
```

Then restart the service:

```bash
docker-compose up -d elasticsearch
```

### Optimize Elasticsearch Refresh Interval

```bash
curl -X PUT "localhost:9200/resources-v1/_settings" \
  -H "Content-Type: application/json" \
  -d '{"index": {"refresh_interval": "5s"}}'
```

### Increase API Worker Count

```bash
# Change command in docker-compose.yml for the API service
command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Increase Crawler Concurrency

```bash
# Set environment variables in docker-compose.yml
crawler:
  environment:
    - CRAWLER_CONCURRENT_REQUESTS=64
```

### Monitor Performance Metrics

```bash
# Install htop if needed
apt-get update && apt-get install -y htop

# Run htop to monitor system resources
htop
```

## Detailed Example Workflows

### Complete Search and Crawl Workflow

1. **Perform a search for a term that may not have many results**:
   ```bash
   curl -X GET "http://localhost:8000/search?q=fortran+array+handling"
   ```

2. **Start a crawler job for this query**:
   ```bash
   curl -X POST "http://localhost:8000/crawl" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "fortran array handling",
       "depth": 3
     }'
   ```

3. **Check the crawler job status**:
   ```bash
   curl -X GET "http://localhost:8000/crawl/status/{job_id}" | jq
   ```

4. **Monitor crawler logs**:
   ```bash
   docker-compose logs -f crawler
   ```

5. **Open a WebSocket connection to see results in real-time**:
   ```bash
   websocat ws://localhost:8001/ws/search?query=fortran+array+handling
   ```

6. **Verify results are being added to Elasticsearch**:
   ```bash
   curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
     -H "Content-Type: application/json" \
     -d '{
       "query": {
         "match": {
           "content": "fortran array handling"
         }
       },
       "sort": [{"timestamp": {"order": "desc"}}]
     }'
   ```

7. **Check Redis for crawler statistics**:
   ```bash
   docker-compose exec redis redis-cli hgetall "crawler:stats:{job_id}"
   ```

### Index Maintenance Workflow

1. **Create a new index version**:
   ```bash
   curl -X PUT "localhost:9200/resources-v2" \
     -H "Content-Type: application/json" \
     -d @elasticsearch/mappings/resources-v2.json
   ```

2. **Reindex data to the new index**:
   ```bash
   curl -X POST "localhost:9200/_reindex?pretty" \
     -H "Content-Type: application/json" \
     -d '{
       "source": {"index": "resources-v1"},
       "dest": {"index": "resources-v2"}
     }'
   ```

3. **Create an alias for the new index**:
   ```bash
   curl -X POST "localhost:9200/_aliases?pretty" \
     -H "Content-Type: application/json" \
     -d '{
       "actions": [
         {"remove": {"index": "resources-v1", "alias": "resources"}},
         {"add": {"index": "resources-v2", "alias": "resources"}}
       ]
     }'
   ```

4. **Update API configuration to use the alias**:
   Edit the API configuration to use the `resources` alias instead of a specific index version.

5. **Verify the alias is working**:
   ```bash
   curl -X GET "http://localhost:8000/search?q=python"
   ```

6. **Remove the old index when no longer needed**:
   ```bash
   curl -X DELETE "localhost:9200/resources-v1"
   ```

### Data Backup Workflow

1. **Register a backup repository**:
   ```bash
   curl -X PUT "localhost:9200/_snapshot/backup_repo" \
     -H "Content-Type: application/json" \
     -d '{
       "type": "fs",
       "settings": {
         "location": "/usr/share/elasticsearch/backup"
       }
     }'
   ```

2. **Create a full snapshot**:
   ```bash
   curl -X PUT "localhost:9200/_snapshot/backup_repo/snapshot_1?wait_for_completion=true"
   ```

3. **List all snapshots**:
   ```bash
   curl -X GET "localhost:9200/_snapshot/backup_repo/_all?pretty"
   ```

4. **Back up Redis data**:
   ```bash
   docker-compose exec redis redis-cli SAVE
   docker cp resource-grep_redis_1:/data/dump.rdb ./redis-backup.rdb
   ```

5. **Back up configuration files**:
   ```bash
   docker cp resource-grep_api_1:/app/config ./config-backup
   ```

## System Stats and Diagnostics

### Get Total Data Size

```bash
# Elasticsearch indices size
curl -X GET "http://localhost:9200/_cat/indices?v&h=index,store.size" | awk '{sum += $2} END {print sum " total"}'

# Redis memory usage
docker-compose exec redis redis-cli info memory | grep used_memory_human

# Container disk usage
docker system df
```

### Get Resource Counts by Type and Language

```bash
# Get count by resource type
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "resource_types": {
        "terms": {
          "field": "type",
          "size": 100
        }
      }
    }
  }'

# Get count by programming language
curl -X GET "http://localhost:9200/resources-v1/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "languages": {
        "terms": {
          "field": "languages",
          "size": 100
        }
      }
    }
  }'
```

### Get System Resource Usage

```bash
# Check container CPU and memory usage
docker stats --no-stream

# Check disk space
df -h

# Check memory usage
free -h
```

### Get API Request Stats

```bash
# Get request count by endpoint
docker-compose logs api | grep "GET\|POST" | sort | uniq -c | sort -nr

# Get average response time
curl -w "\nConnection: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" http://localhost:8000/search?q=python
``` 