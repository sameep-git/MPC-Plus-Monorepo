FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# Specifically need libpq-dev for psycopg2 compilation if using psycopg2 and not psycopg2-binary, 
# but installing it anyway for safety.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend app source code
COPY . .

# Environment setup
ENV PYTHONPATH=/app

# Start the watchdog
ENTRYPOINT ["python", "-m", "src.data_manipulation.file_monitoring.folder_monitor"]
