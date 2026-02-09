# ── Stage 1: Build dependencies ──────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.4

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export to requirements.txt (avoids needing Poetry in production)
RUN poetry export --without dev --format requirements.txt --output requirements.txt

# Install into a virtual-env so we can copy it cleanly
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Production runtime ─────────────────────────────
FROM python:3.11-slim AS runtime

# Security: run as non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy virtual-env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY app ./app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check — matches /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn (production settings)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
