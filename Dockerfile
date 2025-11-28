# GeoGuessr MCP Server Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY server.py .

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["python", "server.py"]