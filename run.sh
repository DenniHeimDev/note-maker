#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".env" ]]; then
  echo "Tips: Køyr python setup.py (GUI) eller python setup_cli.py (CLI) for å konfigurere mapper og API-nøkkel."
fi

read_env_value() {
  local requested_key="$1"
  python3 - "$requested_key" <<'PY'
import sys
from pathlib import Path

key = sys.argv[1]

def read_value(path: Path):
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                name, value = stripped.split("=", 1)
                name = name.strip()
                value = value.strip()
            else:
                name = "OPENAI_API_KEY"
                value = stripped
            if not value:
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if name == key:
                print(value, end="")
                return value
    return None

for candidate in (Path('.env'), Path('_main.env')):
    value = read_value(candidate)
    if value is not None:
        break
PY
}

ensure_openai_key() {
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    return
  fi

  local key
  key="$(read_env_value OPENAI_API_KEY)"
  if [[ -n "${key:-}" ]]; then
    export OPENAI_API_KEY="$key"
  fi
}

ensure_openai_key

CONFIG_INPUT_PATH="$(read_env_value HOST_INPUT_PATH)"
CONFIG_OUTPUT_PATH="$(read_env_value HOST_OUTPUT_PATH)"
CONFIG_COPY_PATH="$(read_env_value HOST_COPY_PATH)"

HOST_INPUT_PATH_DEFAULT="${HOST_INPUT_PATH:-${CONFIG_INPUT_PATH:-/mnt/c/Users/denni/Downloads}}"
HOST_OUTPUT_PATH_DEFAULT="${HOST_OUTPUT_PATH:-${CONFIG_OUTPUT_PATH:-"/mnt/c/Users/denni/Telia Sky/Obsidian/DenniHeim's Vault/1. Projects/FORKURS"}}"
HOST_COPY_PATH_DEFAULT="${HOST_COPY_PATH:-${CONFIG_COPY_PATH:-$HOST_OUTPUT_PATH_DEFAULT}}"

HOST_INPUT_PATH="$(realpath -m "$HOST_INPUT_PATH_DEFAULT")"
HOST_OUTPUT_PATH="$(realpath -m "$HOST_OUTPUT_PATH_DEFAULT")"
HOST_COPY_PATH="$(realpath -m "$HOST_COPY_PATH_DEFAULT")"

mkdir -p "$HOST_INPUT_PATH" "$HOST_OUTPUT_PATH" "$HOST_COPY_PATH"

export HOST_INPUT_PATH
export HOST_OUTPUT_PATH
export HOST_COPY_PATH

echo "Mapper brukt i denne økta:"
echo "  Inndata:    $HOST_INPUT_PATH"
echo "  Notat:      $HOST_OUTPUT_PATH"
echo "  Kopi:       $HOST_COPY_PATH"

echo "Bygg og start konteinaren ..."
echo "Opne http://localhost:8000 i nettlesaren din når konteinaren køyrer."
docker compose up --build "$@"
