# ── Stage 1: deps ─────────────────────────────────────────────────────────────
FROM python:3.13-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libxml2-dev libxslt-dev libffi-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.3.2

COPY pyproject.toml poetry.lock ./

# Install production dependencies into the system Python so the final image
# does not need Poetry at runtime.
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-root


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Runtime shared libraries required by lxml (newspaper4k dependency)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /usr/local/lib/python3.13/site-packages \
                 /usr/local/lib/python3.13/site-packages
COPY --from=deps /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY . .

RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8002"]
