# GeoGuessr MCP Server Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install --no-cache-dir uv

# Copy only dependency files for better layer caching
COPY pyproject.toml .

# Install Python dependencies from pyproject.toml
RUN uv pip install --system --no-cache -e .

# Copy application source code
COPY src/ ./src/

# Create data directory for schema cache
RUN mkdir -p /app/data/schemas

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server using the installed package entry point
CMD ["python", "-m", "geoguessr_mcp.main"]