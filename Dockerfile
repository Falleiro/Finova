# ─── Stage 1: Builder ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a prefix
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ─── Stage 2: Runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create directory for temporary chart files
RUN mkdir -p /tmp/finova_charts

# Create non-root user for security
RUN useradd -m -u 1000 finova && chown -R finova:finova /app /tmp/finova_charts
USER finova

# Copy source code
COPY --chown=finova:finova . .

# Ensure data directory exists (volume is mounted by Railway externally)
RUN mkdir -p /app/data

# Health check — verifies the process is alive
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os; os.path.exists('/app/data/finova.db') or exit(0)" || exit 1

CMD ["python", "main.py"]
