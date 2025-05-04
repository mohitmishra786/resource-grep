# Resource Grep

Resource Grep is a real-time search engine for programming resources, designed to instantly find relevant developer resources like tutorials, documentation, code snippets, and articles from across the entire internet.

## Features

- **Comprehensive Internet Search** - Searches the entire internet for programming resources without limitations
- **Real-time search** - Instantly find programming resources as you type
- **Live WebSocket updates** - See new resources as they're discovered in real-time
- **Intelligent crawling** - Automatically crawls the web when new search terms are entered
- **Support for all programming languages** - From modern languages like Python and JavaScript to legacy systems like COBOL and FORTRAN
- **Filtering** - Filter results by resource type and programming language
- **Code snippets** - Extract and view relevant code snippets from resources
- **Smart quality scoring** - Resources are scored by relevance and quality

## Documentation

- [**API Reference**](API.md) - Complete reference for the Resource Grep HTTP and WebSocket APIs
- [**Architecture**](ARCHITECTURE.md) - Detailed technical architecture and system design
- [**Deployment Guide**](DEPLOYMENT.md) - Instructions for deploying Resource Grep in different environments
- [**Operations Playbook**](PLAYBOOK.md) - Comprehensive guide for operating and troubleshooting
- [**Contributing Guide**](CONTRIBUTING.md) - Guidelines for contributing to Resource Grep
- [**System Statistics**](STATISTICS.md) - Current data statistics and performance metrics

## Quick Start

### Prerequisites

- Docker and Docker Compose

### Running the Project

1. Clone the repository:
   ```
   git clone https://github.com/username/resource-grep.git
   cd resource-grep
   ```

2. Start the services:
   ```
   docker-compose up -d
   ```

3. Access the frontend:
   ```
   http://localhost:80
   ```

## How it Works

1. **Search Initiation**: When a user searches for any programming topic:
   - The query is sent to both the HTTP API and WebSocket API
   - The frontend automatically falls back to the most reliable method
   - The API returns immediate results from the current index
   
2. **Unlimited Crawling**: For new or low-result queries:
   - A crawler job is automatically started
   - The crawler searches across the entire internet with minimal restrictions
   - Uses intelligent URL selection to find relevant resources
   - Resources are indexed in real-time
   
3. **Live Results**: As the crawler discovers new resources:
   - They are immediately indexed in Elasticsearch
   - Updates are pushed to connected clients via WebSockets
   - Users see new results appear without refreshing

4. **Smart Resource Processing**:
   - Resources are analyzed for code snippets, relevance, and quality
   - Content is classified by type (tutorial, documentation, article, etc.)
   - Resources are scored for relevance to the query
   - Special handling for legacy programming languages

## System Architecture

Resource Grep uses a modern microservices architecture with Docker Compose:

```
┌─────────────────────────────────────┐
│           Docker Compose            │
├─────────┬─────────┬─────────┬───────┤
│  API &  │         │         │       │
│ Stream  │ Elastic │  Redis  │Crawler│
│ Services│ search  │         │       │
└─────────┴─────────┴─────────┴───────┘
```

### Components

- **Frontend**: Static HTML/JS/CSS served by Nginx with automatic fallback between HTTP and WebSocket modes
- **API**: FastAPI backend for HTTP search queries
- **Streaming API**: WebSocket server for real-time search results
- **Crawler**: Advanced Scrapy-based web crawler with comprehensive internet search capabilities
- **Search Engine**: Elasticsearch-based search with relevance scoring
- **Redis**: Used for messaging and real-time updates
- **Elasticsearch**: Stores and indexes resource data

For more detailed information about the architecture, see the [ARCHITECTURE.md](ARCHITECTURE.md) document.

## API Examples

### HTTP Search API
```bash
curl -X GET "http://localhost:8000/search?q=python+tutorial"
```

### WebSocket API (for live updates)
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/search?query=python+tutorial');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New result:', data);
};
```

For a complete API reference, see the [API.md](API.md) document.

## Advanced Features

### Intelligent Crawling

The crawler employs sophisticated strategies to find the most relevant resources:

1. **Unrestricted Internet Search**: Capable of searching the entire internet without artificial limitations
   - Disabled robots.txt restrictions for comprehensive crawling
   - Increased concurrent requests and reduced delay for faster crawling
   - Increased depth limit and timeout for more thorough exploration
   - Special handling for search engines like Google, Bing, DuckDuckGo, and more

2. **Priority Domains**: Focuses on quality programming resources from sites like:
   - GitHub, Stack Overflow, Medium, Dev.to
   - Official documentation sites
   - Educational platforms
   - Legacy programming resources
   - Academic and research sites
   
3. **Resource Detection**: Uses multiple signals to identify valuable content:
   - Presence of code snippets
   - Technical keyword density
   - Page structure analysis
   - Domain authority
   - Special handling for legacy programming languages

## Project Structure

```
resource-grep/
├── api/                 # HTTP API service
├── crawler/             # Web crawler based on Scrapy
├── streaming/           # WebSocket streaming service
├── static/              # Frontend static files
├── elasticsearch/       # Elasticsearch mappings and config
├── scripts/             # Utility scripts
├── tests/               # Test files
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile.*         # Dockerfiles for each service
├── README.md            # This file
├── ARCHITECTURE.md      # Architecture documentation
├── API.md               # API reference
├── DEPLOYMENT.md        # Deployment guide
├── PLAYBOOK.md          # Operations playbook
└── CONTRIBUTING.md      # Contributing guidelines
```

## Contributing

We welcome contributions to Resource Grep! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the LICENSE file for details.