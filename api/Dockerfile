FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Scrapy for the crawler integration
RUN pip install scrapy

# Install the crawler package in development mode
COPY crawler /app/crawler
WORKDIR /app/crawler
RUN pip install -e .
WORKDIR /app

# No need to copy files here as they will be mounted as volumes

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
