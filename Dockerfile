FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts ./scripts
COPY data ./data

# Create workdir for job output
RUN mkdir -p /app/workdir

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV WORKDIR=/app/workdir

# Default command: run API
CMD ["uvicorn", "scripts.main:app", "--host", "0.0.0.0", "--port", "8000"]
