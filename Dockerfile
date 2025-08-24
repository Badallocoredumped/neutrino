# Dockerfile
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
COPY config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code to the right location
COPY src/ ./src/

# Create necessary directories with proper permissions
RUN mkdir -p raw transformed logs data && \
    chown -R appuser:appuser /app

# Make Python scripts executable (update paths to src/)
RUN chmod +x src/scheduler.py src/etl_energy_data.py

# Set environment variables
ENV PYTHONPATH=/app:/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Expose port for health checks (optional)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - start scheduler from src/ directory
CMD ["python", "src/scheduler.py"]