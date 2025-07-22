FROM python:3.11-slim

# Environment flags
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all source code
COPY . .

# Clear all proxy-related environment variables to prevent OpenAI SDK errors
ENV HTTP_PROXY= \
    HTTPS_PROXY= \
    http_proxy= \
    https_proxy= \
    ALL_PROXY= \
    all_proxy=

# Expose default port
EXPOSE 5000

# Run using Python directly
CMD ["python", "Agentic_Rag/main_rag_integrated.py"]
