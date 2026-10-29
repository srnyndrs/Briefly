#!/bin/sh
set -eu

: "${OLLAMA_MODEL:?OLLAMA_MODEL is required}"
ollama serve &
server_pid=$!
cleanup() {
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

attempt=0
until ollama list >/dev/null 2>&1; do
    kill -0 "$server_pid"
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        echo 'Ollama did not start within 30 seconds.' >&2
        exit 1
    fi
    sleep 1
done

if ollama show "$OLLAMA_MODEL" >/dev/null 2>&1; then
    echo "Using cached model: $OLLAMA_MODEL"
else
    echo "Downloading model: $OLLAMA_MODEL"
    ollama pull "$OLLAMA_MODEL"
fi
ollama show "$OLLAMA_MODEL" >/dev/null
wait "$server_pid"
