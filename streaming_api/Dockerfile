FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir fastapi uvicorn redis websockets aioredis async-timeout aiohttp elasticsearch==8.10.0

# Copy streaming API code
COPY streaming_api /app/streaming_api

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Run the streaming API
CMD ["uvicorn", "streaming_api.streaming:app", "--host", "0.0.0.0", "--port", "8001"] 