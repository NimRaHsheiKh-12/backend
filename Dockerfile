# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first (cache layer optimization)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY ./src ./src

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
