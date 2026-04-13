#!/bin/sh
set -eu

required_vars="TOKEN SECRET_KEY"

for var_name in $required_vars; do
  var_value="$(eval "printf '%s' \"\${$var_name:-}\"")"
  if [ -z "$var_value" ]; then
    echo "Missing required environment variable: $var_name" >&2
    exit 1
  fi
done

DATA_DIR="${DATA_DIR:-/app/data}"
mkdir -p "$DATA_DIR"

exec "$@"
