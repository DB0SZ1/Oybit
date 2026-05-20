FROM python:3.11-slim

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (required for scraping)
RUN playwright install chromium
RUN playwright install-deps

# Copy the rest of the application code
COPY . .

# Hugging Face Spaces strictly requires port 7860
EXPOSE 7860

# Run FastAPI via Uvicorn bound to 0.0.0.0 and port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
