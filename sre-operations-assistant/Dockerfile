FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to fix CVEs
RUN pip install --upgrade pip setuptools>=75.6.0

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy all source files
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV AWS_DEFAULT_REGION=us-west-2

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the MCP server with uvicorn for production
CMD ["uvicorn", "src.mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]