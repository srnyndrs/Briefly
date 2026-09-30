FROM python:3.13-slim AS deps

WORKDIR /app

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN pip install --no-cache-dir poetry==2.3.2

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-interaction


FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=deps /app/.venv /app/.venv
COPY src ./src

RUN useradd --create-home --shell /bin/false appuser
USER appuser

EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8002"]
