# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better build cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your server code
COPY server.py .

# Expose the port Flask runs on
EXPOSE 8085

# Run the server
CMD ["python", "server.py"]
