FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency metadata and install dependencies first
COPY pyproject.toml setup.py /app/
RUN mkdir -p /app/rdn && touch /app/rdn/__init__.py \
    && pip install --no-cache-dir .[full]

# Copy the rest of the application files
COPY . /app/

# Reinstall the package to copy actual code files
RUN pip install --no-cache-dir .[full]

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose Streamlit dashboard and memory node ports
EXPOSE 8501 8765

ENTRYPOINT ["/app/docker-entrypoint.sh"]
