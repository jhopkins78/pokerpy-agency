FROM python:3.11-slim

# Install build tools and system libraries
RUN apt-get update && apt-get install -y \
    gcc g++ build-essential \
    libffi-dev libssl-dev libc-dev \
    curl libstdc++6

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy rest of the app
COPY . .

# Set environment vars
ENV FLASK_APP=Agentic-Rag/main_rag_integrated.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python", "Agentic-Rag/main_rag_integrated.py"]
