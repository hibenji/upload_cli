# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better build cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your server code and templates
COPY server.py .
COPY templates ./templates

# Expose the port Flask runs on
EXPOSE 8086

# Run the server
CMD ["gunicorn", "--bind", "0.0.0.0:8086", "--workers", "2", "--threads", "4", "--timeout", "300", "server:app"]
