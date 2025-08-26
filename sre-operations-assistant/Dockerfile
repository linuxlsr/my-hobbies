FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to fix CVEs
RUN pip install --upgrade pip setuptools>=75.6.0

# Install all dependencies
RUN pip install fastapi uvicorn boto3 requests pydantic

# Copy all source files
COPY src/ ./src/
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the full MCP server
CMD ["python", "src/mcp_server.py"]