FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . /app/

# Make start script executable
RUN chmod +x /app/start.sh

# Expose both ports
# 8000 → FastAPI backend API
# 8501 → Streamlit frontend (main user-facing interface)
EXPOSE 8000
EXPOSE 8501

# Use bash explicitly so the & background operator works correctly
CMD ["bash", "/app/start.sh"]
