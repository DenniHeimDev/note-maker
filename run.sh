#!/usr/bin/env bash
set -euo pipefail

#if [[ -z "${OPENAI_API_KEY:-}" ]]; then
#  echo "Feil: OPENAI_API_KEY er ikkje sett i miljøet." >&2
#  echo "Eksporter nøkkelen før du køyrer skriptet, t.d.:" >&2
#  echo "  export OPENAI_API_KEY=sk-..." >&2
#  exit 1
#fi

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
