FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Search engine doesn't need its own service since it's used by the API
CMD ["echo", "Search module is imported by the API"]