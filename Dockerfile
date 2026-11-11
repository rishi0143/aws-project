
FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create database storage directory
RUN mkdir -p /app/data

# Set database path
ENV DATABASE_PATH=/app/data/easybus.db

# Expose Flask/Gunicorn port
EXPOSE 5000

# Start application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
