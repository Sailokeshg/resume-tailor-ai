FROM python:3.11-slim

# Install curl, ca-certificates, and tectonic LaTeX engine
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates fontconfig \
    && curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh \
    && mv tectonic /usr/local/bin/ \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Expose FastAPI on dynamic port for cloud deployments
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
