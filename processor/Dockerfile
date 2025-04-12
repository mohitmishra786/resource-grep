FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# No need to copy files here as they will be mounted as volumes

CMD ["python", "processor/main.py", "--daemon"]