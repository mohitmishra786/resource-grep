# Resource Grep Deployment Guide

This guide provides detailed instructions for deploying Resource Grep in different environments, from local development to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Scaling Considerations](#scaling-considerations)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying Resource Grep, ensure you have the following prerequisites:

- Docker and Docker Compose (v20.10.0+)
- Git
- Python 3.9+ (for non-Docker development)
- At least 4GB of RAM (8GB+ recommended)
- 10GB+ of free disk space
- Internet connection for crawling

## Local Development Setup

For local development, you can run Resource Grep directly on your machine:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/resource-grep/resource-grep.git
   cd resource-grep
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r crawler/requirements.txt
   ```

4. **Start the required services**:
   ```bash
   # Start Elasticsearch
   docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 \
     -e "discovery.type=single-node" \
     -e "xpack.security.enabled=false" \
     -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
     docker.elastic.co/elasticsearch/elasticsearch:7.17.0

   # Start Redis
   docker run -d --name redis -p 6379:6379 redis:6.2
   ```

5. **Initialize the database**:
   ```bash
   python scripts/init_db.py
   ```

6. **Start the API service**:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

7. **Start the streaming service**:
   ```bash
   uvicorn streaming.main:app --reload --port 8001
   ```

8. **Start the crawler (in a new terminal window)**:
   ```bash
   cd crawler
   scrapy crawl resource_spider
   ```

9. **Access the web interface**:
   Open your browser and navigate to `http://localhost:8000`

## Docker Deployment

For a more isolated and reproducible environment, deploy using Docker Compose:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/resource-grep/resource-grep.git
   cd resource-grep
   ```

2. **Build and start the services**:
   ```bash
   docker-compose up -d
   ```

   This command builds and starts all the necessary services:
   - Elasticsearch
   - Redis
   - API Service
   - Streaming Service
   - Crawler Service
   - Web Server (Nginx)

3. **Initialize the database**:
   ```bash
   docker-compose exec api python scripts/init_db.py
   ```

4. **Access the web interface**:
   Open your browser and navigate to `http://localhost`

### Docker Compose Configuration

The `docker-compose.yml` file defines all services required for Resource Grep:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data
    networks:
      - resource-grep

  redis:
    image: redis:6.2
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    networks:
      - resource-grep

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      - ELASTICSEARCH_HOST=elasticsearch
      - REDIS_HOST=redis
    ports:
      - "8000:8000"
    depends_on:
      - elasticsearch
      - redis
    networks:
      - resource-grep

  streaming:
    build:
      context: .
      dockerfile: Dockerfile.streaming
    environment:
      - ELASTICSEARCH_HOST=elasticsearch
      - REDIS_HOST=redis
    ports:
      - "8001:8001"
    depends_on:
      - elasticsearch
      - redis
    networks:
      - resource-grep

  crawler:
    build:
      context: .
      dockerfile: Dockerfile.crawler
    environment:
      - ELASTICSEARCH_HOST=elasticsearch
      - REDIS_HOST=redis
    depends_on:
      - elasticsearch
      - redis
    networks:
      - resource-grep

  web:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./static:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - api
      - streaming
    networks:
      - resource-grep

networks:
  resource-grep:
    driver: bridge

volumes:
  esdata:
    driver: local
  redisdata:
    driver: local
```

## Production Deployment

For production environments, additional configurations are needed for security, scaling, and reliability:

### Architecture

In production, a recommended architecture is:

1. **Load Balancer** (e.g., Nginx, HAProxy) for API and Streaming services
2. **Multiple API instances** for high availability
3. **Multiple Streaming instances** with sticky sessions
4. **Elasticsearch Cluster** with at least 3 nodes
5. **Redis Cluster** for high availability
6. **Multiple Crawler instances** for distributed crawling

### Kubernetes Deployment

1. **Prerequisites**:
   - Kubernetes cluster (v1.20+)
   - kubectl configured to access your cluster
   - Helm (v3.0+)

2. **Deploy Elasticsearch**:
   ```bash
   helm repo add elastic https://helm.elastic.co
   helm install elasticsearch elastic/elasticsearch \
     --set replicas=3 \
     --set esJavaOpts="-Xmx2g -Xms2g" \
     --set resources.limits.cpu=2 \
     --set resources.limits.memory=4Gi \
     --set resources.requests.cpu=1 \
     --set resources.requests.memory=2Gi
   ```

3. **Deploy Redis**:
   ```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm install redis bitnami/redis \
     --set cluster.enabled=true \
     --set cluster.slaveCount=2
   ```

4. **Deploy Resource Grep services**:
   ```bash
   kubectl apply -f k8s/
   ```

   The `k8s/` directory contains all necessary Kubernetes manifest files:
   - Deployments for all services
   - Services for network access
   - ConfigMaps for configuration
   - Secrets for sensitive data
   - Ingress for external access

5. **Scale services as needed**:
   ```bash
   kubectl scale deployment api --replicas=3
   kubectl scale deployment streaming --replicas=2
   kubectl scale deployment crawler --replicas=5
   ```

## Scaling Considerations

### Vertical Scaling

Resource Grep components have different resource requirements:

- **Elasticsearch**: CPU and memory intensive. Allocate at least 2GB of heap memory.
- **Redis**: Memory intensive. Size according to expected key count.
- **API Service**: CPU bound. Scale CPU cores as traffic increases.
- **Streaming Service**: Connection bound. Consider connection count limits.
- **Crawler Service**: Network and CPU bound. Scale based on crawl workload.

### Horizontal Scaling

- **API Service**: Stateless, can be scaled horizontally without constraints.
- **Streaming Service**: Use sticky sessions or Redis for connection state.
- **Crawler Service**: Use Redis to coordinate between instances.
- **Elasticsearch**: Add nodes to the cluster, with consideration for shard allocation.
- **Redis**: Use Redis Cluster for horizontal scaling.

## Environment Variables

Resource Grep services are configured via environment variables:

### Common Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging verbosity level | `INFO` |
| `ELASTICSEARCH_HOST` | Elasticsearch host | `localhost` |
| `ELASTICSEARCH_PORT` | Elasticsearch port | `9200` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_PASSWORD` | Redis password (if any) | `None` |

### API Service Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API service host | `0.0.0.0` |
| `API_PORT` | API service port | `8000` |
| `MAX_SEARCH_RESULTS` | Maximum search results per page | `100` |
| `ENABLE_CORS` | Enable CORS for API endpoints | `true` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit per minute | `60` |

### Streaming Service Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAMING_HOST` | Streaming service host | `0.0.0.0` |
| `STREAMING_PORT` | Streaming service port | `8001` |
| `MAX_CONNECTIONS` | Maximum WebSocket connections | `1000` |
| `HEARTBEAT_INTERVAL` | WebSocket heartbeat interval (seconds) | `30` |

### Crawler Service Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CRAWLER_CONCURRENT_REQUESTS` | Concurrent requests per spider | `32` |
| `CRAWLER_DOWNLOAD_DELAY` | Delay between requests (seconds) | `0.25` |
| `CRAWLER_DEPTH_LIMIT` | Maximum crawl depth | `5` |
| `RESPECT_ROBOTS_TXT` | Whether to respect robots.txt | `false` |
| `USER_AGENT` | User agent for crawler requests | `ResourceGrepBot/1.0` |
| `MAX_ITEMS_PER_DOMAIN` | Maximum items to crawl per domain | `100` |

## Database Setup

### Elasticsearch Setup

1. **Create the resources index**:
   ```bash
   curl -X PUT "localhost:9200/resources-v1" -H "Content-Type: application/json" -d @elasticsearch/mappings/resources.json
   ```

2. **Create the crawler jobs index**:
   ```bash
   curl -X PUT "localhost:9200/crawler-jobs" -H "Content-Type: application/json" -d @elasticsearch/mappings/crawler-jobs.json
   ```

3. **Create index templates**:
   ```bash
   curl -X PUT "localhost:9200/_template/resources" -H "Content-Type: application/json" -d @elasticsearch/templates/resources.json
   ```

### Elasticsearch Index Mappings

The `resources-v1` index has custom mappings for optimal search performance:

```json
{
  "mappings": {
    "properties": {
      "url": { "type": "keyword" },
      "title": { 
        "type": "text",
        "analyzer": "english",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "description": { "type": "text", "analyzer": "english" },
      "content": { "type": "text", "analyzer": "english" },
      "code_snippets": { "type": "text" },
      "domain": { "type": "keyword" },
      "type": { "type": "keyword" },
      "languages": { "type": "keyword" },
      "frameworks": { "type": "keyword" },
      "authors": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "published_date": { "type": "date" },
      "quality_score": { "type": "float" },
      "popularity_score": { "type": "float" },
      "readability_score": { "type": "float" }
    }
  }
}
```

## Monitoring Setup

### Prometheus Configuration

1. **Create a Prometheus configuration file** (`prometheus.yml`):
   ```yaml
   global:
     scrape_interval: 15s
     evaluation_interval: 15s

   scrape_configs:
     - job_name: 'resource-grep-api'
       static_configs:
         - targets: ['api:8000']

     - job_name: 'resource-grep-streaming'
       static_configs:
         - targets: ['streaming:8001']

     - job_name: 'elasticsearch'
       static_configs:
         - targets: ['elasticsearch:9200']

     - job_name: 'redis'
       static_configs:
         - targets: ['redis:6379']
   ```

2. **Deploy Prometheus**:
   ```bash
   docker run -d --name prometheus \
     -p 9090:9090 \
     -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
     prom/prometheus
   ```

### Grafana Dashboard

1. **Deploy Grafana**:
   ```bash
   docker run -d --name grafana \
     -p 3000:3000 \
     grafana/grafana
   ```

2. **Configure Grafana**:
   - Access Grafana at `http://localhost:3000` (default credentials: admin/admin)
   - Add Prometheus as a data source
   - Import the Resource Grep dashboard from `monitoring/grafana-dashboard.json`

## Backup and Recovery

### Elasticsearch Backups

1. **Register a snapshot repository**:
   ```bash
   curl -X PUT "localhost:9200/_snapshot/backup" -H "Content-Type: application/json" -d'
   {
     "type": "fs",
     "settings": {
       "location": "/usr/share/elasticsearch/backup"
     }
   }'
   ```

2. **Create a snapshot**:
   ```bash
   curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
   ```

3. **Restore from a snapshot**:
   ```bash
   curl -X POST "localhost:9200/_snapshot/backup/snapshot_1/_restore"
   ```

### Redis Backups

Redis is configured to persist data to disk using RDB and AOF:

1. **Manual backup**:
   ```bash
   # Inside Redis container
   redis-cli SAVE
   ```

2. **Copy the RDB file**:
   ```bash
   docker cp redis:/data/dump.rdb ./redis-backup.rdb
   ```

3. **Restore from backup**:
   ```bash
   docker cp ./redis-backup.rdb redis:/data/dump.rdb
   docker restart redis
   ```

## Troubleshooting

### Common Issues

#### API Service Not Starting

**Issue**: The API service fails to start with connection errors to Elasticsearch or Redis.
**Solution**: 
1. Check if Elasticsearch and Redis are running: `docker ps`
2. Verify the connection settings in environment variables
3. Check the logs: `docker logs resource-grep-api`

#### Crawler Not Finding Results

**Issue**: The crawler runs but doesn't discover resources.
**Solution**:
1. Check crawler settings, especially USER_AGENT and RESPECT_ROBOTS_TXT
2. Verify Elasticsearch connectivity
3. Increase MAX_DEPTH for deeper crawling
4. Check the crawler logs: `docker logs resource-grep-crawler`

#### WebSocket Connection Failures

**Issue**: WebSocket connections fail or disconnect frequently.
**Solution**:
1. Check if the Streaming service is running
2. Verify browser WebSocket support
3. Check for firewall or proxy issues
4. Increase connection timeout settings
5. Check the streaming logs: `docker logs resource-grep-streaming`

#### Elasticsearch Performance Issues

**Issue**: Elasticsearch is slow or unresponsive.
**Solution**:
1. Increase memory allocation for Elasticsearch
2. Check disk I/O performance
3. Optimize index settings and mappings
4. Consider adding more nodes to the cluster
5. Check Elasticsearch logs: `docker logs elasticsearch`

### Diagnostics Commands

#### Check Service Status
```bash
docker-compose ps
```

#### View Service Logs
```bash
docker-compose logs -f api
docker-compose logs -f streaming
docker-compose logs -f crawler
docker-compose logs -f elasticsearch
docker-compose logs -f redis
```

#### Check Elasticsearch Health
```bash
curl -X GET "localhost:9200/_cluster/health?pretty"
```

#### Check Elasticsearch Indices
```bash
curl -X GET "localhost:9200/_cat/indices?v"
```

#### Check Redis Status
```bash
docker-compose exec redis redis-cli info
```

#### Test API Endpoint
```bash
curl -X GET "localhost:8000/search?q=python&pretty"
```

#### Test WebSocket Connection
```bash
# Using websocat tool
websocat ws://localhost:8001/ws/search?query=python
``` 