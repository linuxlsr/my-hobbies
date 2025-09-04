FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY web/ ./web/
COPY cli/ ./cli/
COPY scripts/start.sh .

# Create data directory and set permissions
RUN mkdir -p data && chmod +x start.sh && chmod 755 data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=5000

# Health check - simplified for ECS
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/ping', timeout=2)" || exit 1

# Start application
CMD ["./start.sh"]