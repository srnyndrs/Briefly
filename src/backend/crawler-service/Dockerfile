# ── Stage 1: dependency install ───────────────────────────────────────────────
FROM python:3.13-slim AS deps

WORKDIR /app

# System libs needed by psycopg2-binary at runtime (already bundled, but
# libpq is needed for connection) and by uvicorn's optional C extensions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (used as the build tool per pyproject.toml)
RUN pip install --no-cache-dir poetry==2.3.2

# Copy dependency manifest first — Docker layer cache means this layer is
# only rebuilt when pyproject.toml / poetry.lock change, not on code changes.
COPY pyproject.toml poetry.lock ./

# Export a plain requirements.txt and install via pip so the final image
# does not need Poetry at runtime.
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-root


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy only installed site-packages from the deps stage
COPY --from=deps /usr/local/lib/python3.13/site-packages \
                 /usr/local/lib/python3.13/site-packages
COPY --from=deps /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Runtime libpq (for psycopg2-binary)
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy application source (respects .dockerignore)
COPY . .

# Run as a non-root user
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8001

# Health-check so docker-compose / Kubernetes know when the service is ready
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001"]
