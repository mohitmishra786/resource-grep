# Resource Grep

Resource Grep is a real-time search engine for programming resources, designed to instantly find relevant developer resources like tutorials, documentation, code snippets, and articles.

## Features

- **Real-time search** - Instantly find programming resources as you type
- **Live WebSocket updates** - See new resources as they're found by the crawler
- **Automatic crawling** - Automatically crawls the web when new search terms are entered
- **Filtering** - Filter results by resource type and programming language
- **Code snippets** - Extract and view relevant code snippets from resources
- **Quality scoring** - Resources are scored by relevance and quality

## Architecture

Resource Grep is built with a microservices architecture using Docker Compose:

![Architecture Diagram]

### Components

- **Frontend** - Static HTML/JS/CSS served by Nginx
- **API** - FastAPI backend for HTTP search queries
- **Streaming API** - WebSocket server for real-time search results
- **Crawler** - Scrapy-based web crawler for finding programming resources
- **Processor** - Processes and indexes crawled content
- **Coordinator** - Distributes crawling tasks
- **Elasticsearch** - Stores and indexes resource data
- **Redis** - Used for messaging and job coordination

## How it Works

1. **Search**: When a user searches for a programming topic, the query is sent to both:
   - The HTTP API for immediate results from the index
   - The WebSocket API for real-time streaming results
   
2. **Indexing**: If no results are found for a query, a crawler job is automatically started
   
3. **Crawling**: The crawler scans the web for relevant resources matching the query
   
4. **Processing**: Found resources are processed, classified, and sent to:
   - Elasticsearch for indexing
   - The WebSocket server for real-time delivery to the client
   
5. **Results**: New results appear in real-time in the UI as they're discovered

## Getting Started

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
   http://localhost:3000
   ```

### Development

- The frontend is in the `static/` directory
- API endpoints are in the `api/main.py` file
- The crawler is in the `crawler/` directory
- Search functionality is in the `search/index.py` file

## Search Types

### HTTP Search
Traditional search that returns results immediately from the index.

### WebSocket (Live) Search
Real-time search that:
1. Returns initial results from the index
2. Streams new results as they're found by the crawler
3. Automatically starts crawling for new topics

## Project Status

This project is currently in development. Currently indexed topics include:
- Python
- React

More topics are being added continuously as the crawler runs.

## License

This project is licensed under the MIT License - see the LICENSE file for details.