# Spotify App Agent Template Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and timezone data
RUN apt-get update && apt-get install -y \
    gcc \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (change to your preferred timezone)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/snapshots /app/state /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for OAuth callback (if needed)
EXPOSE 8888

# No health check - simple process monitoring is sufficient

# Run the application
CMD ["python", "-m", "app.main"]
