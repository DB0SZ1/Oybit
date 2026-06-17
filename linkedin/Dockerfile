# Use the official Playwright image which includes all OS dependencies for Chromium
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the correct version of playwright browsers
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Hugging Face Spaces exposes port 7860 by default
ENV PORT=7860

# Expose the port
EXPOSE 7860

# Command to run the application
CMD ["python", "main.py"]
