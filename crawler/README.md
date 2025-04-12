# Resource Crawler

This directory contains the crawler implementation for the resource-grep project.

## Architecture

The crawler has two operation modes:

### 1. Standalone Mode

The standalone crawler uses `ResourceSpider` (in `resource_crawler/spiders/resource_spider.py`) and is executed through:
- The `run_crawler.py` script (for manual execution)
- The Docker container defined in `Dockerfile` (for production)

### 2. Distributed Mode

The distributed crawler uses `DistributedResourceSpider` (in `resource_crawler/spiders/distributed_spider.py`) and is:
- Managed by the coordinator service (`coordinator/coordinator.py`)
- Supports multiple worker instances running in parallel
- Uses Redis for coordination, URL queue management and results distribution

## Running the Crawler

### Standalone Mode

```bash
# From the crawler directory
python run_crawler.py "search query"
```

### Distributed Mode

The distributed crawler is managed by the coordinator service and should be run using docker-compose:

```bash
docker-compose up coordinator
```

## Configuration

Spider settings are defined in `resource_crawler/settings.py`. 