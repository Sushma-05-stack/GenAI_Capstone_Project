FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/chroma_store

EXPOSE 8000

# Use $PORT from Render (falls back to 8000 locally)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
