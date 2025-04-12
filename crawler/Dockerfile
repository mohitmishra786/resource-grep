FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the crawler code
COPY crawler /app/crawler

# Install the crawler package in development mode
WORKDIR /app/crawler
RUN pip install -e .

# Set environment variables
ENV PYTHONPATH=/app
ENV SCRAPY_SETTINGS_MODULE=resource_crawler.settings
ENV PYTHONUNBUFFERED=1

# Create a script to run the crawler
RUN echo '#!/bin/bash\n\
cd /app/crawler\n\
while true; do\n\
  scrapy crawl resource_spider -a search_query=python || true\n\
  sleep 60\n\
done' > /app/run.sh && \
chmod +x /app/run.sh

# Run the crawler
CMD ["/app/run.sh"]