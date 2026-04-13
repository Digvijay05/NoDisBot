#!/bin/sh
set -eu

required_vars="TOKEN SECRET_KEY NOTION_API_KEY NOTION_DB_ID"

for var_name in $required_vars; do
  var_value="$(eval "printf '%s' \"\${$var_name:-}\"")"
  if [ -z "$var_value" ]; then
    echo "Missing required environment variable: $var_name" >&2
    exit 1
  fi
done

OLLAMA_API_VALUE="${OLLAMA_API:-${OLLAMA_API_KEY:-}}"
if [ -z "$OLLAMA_API_VALUE" ]; then
  echo "Missing required environment variable: OLLAMA_API (or OLLAMA_API_KEY)" >&2
  exit 1
fi

export OLLAMA_URL="${OLLAMA_URL:-https://ollama.com}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-deepseek-v3.1:671b-cloud}"
export OLLAMA_API="$OLLAMA_API_VALUE"
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-$OLLAMA_API_VALUE}"

DATA_DIR="${DATA_DIR:-/app/data}"
mkdir -p "$DATA_DIR"

exec "$@"
