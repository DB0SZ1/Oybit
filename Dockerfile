FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers and Ubuntu dependencies are already pre-installed in this base image!
# No need to run playwright install-deps.

# Copy the rest of the application code
COPY . .

# Hugging Face Spaces strictly requires port 7860
EXPOSE 7860

# Run FastAPI via Uvicorn bound to 0.0.0.0 and port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
