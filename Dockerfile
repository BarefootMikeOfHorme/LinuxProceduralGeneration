# VaultMind Forge - Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Python dependencies
FROM python:3.12-slim as python-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Node.js web UI build
FROM node:18-slim as node-builder

WORKDIR /app/web_ui

# Copy web UI package files
COPY web_ui/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy web UI source
COPY web_ui/ ./

# Build web UI
RUN npm run build

# Stage 3: Final production image
FROM python:3.12-slim

# Set minimal environment variables (user configures the rest via .env or docker-compose)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=python-builder /root/.local /root/.local

# Copy application code
COPY backend/ ./backend/
COPY vaultmind_forge/ ./vaultmind_forge/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE.md ./

# Copy built web UI
COPY --from=node-builder /app/web_ui/dist ./web_ui/dist

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/output /app/models /app/checkpoints

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application (configure via environment variables or .env file)
CMD ["python", "-m", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
