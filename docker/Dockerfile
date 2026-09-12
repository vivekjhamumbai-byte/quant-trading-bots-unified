FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV TRADING_MODE=paper

# Expose dashboard port
EXPOSE 8765

# Run based on SERVICE type
ARG SERVICE=dashboard
ARG BOT_NAME=

RUN echo "SERVICE: $SERVICE, BOT_NAME: $BOT_NAME"

# Default to dashboard
CMD ["python", "dashboard.py"]
