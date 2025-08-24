# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Emir Ozen <emirozen@stu.khas.edu.tr>"
LABEL description="Neutrino Energy Data Pipeline - Real-time energy monitoring system"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p raw transformed logs data && \
    chown -R appuser:appuser /app

# Copy and make wait script executable
COPY docker-scripts/wait-for-it.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Make Python scripts executable
RUN chmod +x scheduler.py etl_energy_data.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Expose port for health checks (optional)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=60s --retries=3 \
    CMD python -c "import requests; import sys; sys.exit(0)" || exit 1

# Default command - wait for dependencies then start scheduler
CMD ["wait-for-it.sh", "mongodb:27017", "--timeout=60", "--", \
     "wait-for-it.sh", "postgres:5432", "--timeout=60", "--", \
     "python", "scheduler.py"]
