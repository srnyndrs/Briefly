FROM ollama/ollama:0.35.1

ARG OLLAMA_MODEL
ENV OLLAMA_MODELS=/opt/ollama/models

RUN set -eu; \
    : "${OLLAMA_MODEL:?OLLAMA_MODEL build argument is required}"; \
    export OLLAMA_HOST=127.0.0.1:11434; \
    ollama serve > /tmp/ollama-build.log 2>&1 & \
    server_pid=$!; \
    trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT; \
    attempt=0; \
    until ollama list >/dev/null 2>&1; do \
        attempt=$((attempt + 1)); \
        if [ "$attempt" -ge 30 ]; then cat /tmp/ollama-build.log; exit 1; fi; \
        sleep 1; \
    done; \
    ollama pull "$OLLAMA_MODEL"; \
    ollama show "$OLLAMA_MODEL" >/dev/null; \
    kill "$server_pid"; \
    wait "$server_pid" || true; \
    trap - EXIT; \
    rm /tmp/ollama-build.log
