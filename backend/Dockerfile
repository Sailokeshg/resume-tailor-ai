FROM python:3.11-slim

# Install tectonic LaTeX engine and ca-certificates
RUN apt-get update \
    && apt-get install -y --no-install-recommends tectonic ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Expose FastAPI on dynamic port for cloud deployments
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
