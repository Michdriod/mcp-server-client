# Multi-stage Dockerfile for Database Query Assistant
# Stage 1: Base image with dependencies
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Stage 2: MCP Server
FROM base as server

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port (if needed for future HTTP server)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import redis; r = redis.from_url('${REDIS_URL}'); r.ping()" || exit 1

# Run MCP server
CMD ["python", "server/mcp_server.py"]


# Stage 3: Celery Worker
FROM base as celery-worker

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check for Celery worker
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD celery -A server.celery_app inspect ping -d celery@$HOSTNAME || exit 1

# Run Celery worker
CMD ["celery", "-A", "server.celery_app", "worker", "--loglevel=info", "--concurrency=4"]


# Stage 4: Celery Beat
FROM base as celery-beat

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check for Celery beat
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD celery -A server.celery_app inspect active || exit 1

# Run Celery beat
CMD ["celery", "-A", "server.celery_app", "beat", "--loglevel=info"]


# Stage 5: Web UI
FROM base as web-ui

# Install Streamlit dependencies
RUN pip install streamlit pandas

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "client/web_ui/app.py", "--server.address=0.0.0.0"]
