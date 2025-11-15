#!/usr/bin/env bash
set -euo pipefail

ensure_openai_key() {
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    return
  fi

  local key
  key="$(python3 - <<'PY'
from pathlib import Path

def read_key(path: Path):
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                name, value = stripped.split("=", 1)
                if name.strip() != "OPENAI_API_KEY":
                    continue
                candidate = value.strip().strip("'\"")
                if candidate:
                    return candidate
            else:
                return stripped
    return None

for candidate in (Path(".env"), Path("_main.env")):
    if not candidate.exists():
        continue
    value = read_key(candidate)
    if value:
        print(value, end="")
        break
PY
)"

  if [[ -n "${key:-}" ]]; then
    export OPENAI_API_KEY="$key"
  fi
}

ensure_openai_key

HOST_INPUT_PATH_DEFAULT="${HOST_INPUT_PATH:-/mnt/c/Users/denni/Downloads}"
HOST_OUTPUT_PATH_DEFAULT="${HOST_OUTPUT_PATH:-"/mnt/c/Users/denni/Telia Sky/Obsidian/DenniHeim's Vault/1. Projects/FORKURS"}"
HOST_COPY_PATH_DEFAULT="${HOST_COPY_PATH:-$HOST_OUTPUT_PATH_DEFAULT}"

HOST_INPUT_PATH="$(realpath -m "$HOST_INPUT_PATH_DEFAULT")"
HOST_OUTPUT_PATH="$(realpath -m "$HOST_OUTPUT_PATH_DEFAULT")"
HOST_COPY_PATH="$(realpath -m "$HOST_COPY_PATH_DEFAULT")"

mkdir -p "$HOST_INPUT_PATH" "$HOST_OUTPUT_PATH" "$HOST_COPY_PATH"

export HOST_INPUT_PATH
export HOST_OUTPUT_PATH
export HOST_COPY_PATH

if [[ "${DISPLAY:-}" == "" ]]; then
  export DISPLAY=":0"
  echo "DISPLAY var ikkje sett. Brukar standard :0."
fi

echo "Bygg og start konteinaren ..."
docker compose up --build "$@"
