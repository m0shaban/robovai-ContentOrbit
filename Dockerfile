# ════════════════════════════════════════════════════════════════════════════════
# ContentOrbit Enterprise - Production Dockerfile
# ════════════════════════════════════════════════════════════════════════════════
# Multi-stage build for optimized production image

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ════════════════════════════════════════════════════════════════════════════════
# Production Stage
# ════════════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim as production

# Labels
LABEL maintainer="ContentOrbit Enterprise"
LABEL version="1.0.0"
LABEL description="Production-grade content automation platform"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=UTC

# Create non-root user for security
RUN groupadd --gid 1000 contentorbit && \
    useradd --uid 1000 --gid contentorbit --shell /bin/bash --create-home contentorbit

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory
WORKDIR /app

# Create data directories
RUN mkdir -p /app/data/logs && \
    chown -R contentorbit:contentorbit /app

# Copy application code
COPY --chown=contentorbit:contentorbit . .

# Switch to non-root user
USER contentorbit

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose ports
# 8501 - Streamlit Dashboard
EXPOSE 8501

# Default command (can be overridden)
CMD ["streamlit", "run", "dashboard/main_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
