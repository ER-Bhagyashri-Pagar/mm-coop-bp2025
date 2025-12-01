# Use official lightweight Python image (compatible with Google libs)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system-level dependencies required by Firestore + PubSub gRPC
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Cloud Run uses port 8080
ENV PORT=8080
EXPOSE 8080

# Start FastAPI worker
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]