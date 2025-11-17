#!/usr/bin/env python3
"""Interactive setup utility for note-maker.

The script collects the folders that should be mounted into the container and
the OpenAI API key, then writes them to the local .env file. Any unrelated
entries that already exist in .env are preserved at the bottom of the file.
"""

from __future__ import annotations

import getpass
import sys
from datetime import datetime
from pathlib import Path

from config_helpers import (
    COPY_FALLBACK,
    ENV_PATH,
    INPUT_FALLBACK,
    OUTPUT_FALLBACK,
    collect_preserved_lines,
    ensure_directory,
    normalize_path,
    parse_env_file,
    preview_key,
    write_env_file,
)


def _prompt_path(message: str, default_value: str) -> str:
    while True:
        prompt = f"{message} [{default_value}]: "
        user_input = input(prompt).strip()
        if not user_input:
            user_input = default_value
        try:
            normalized = normalize_path(user_input)
        except Exception as exc:  # pragma: no cover - interactive helper
            print(f"Kunne ikkje tolke stien ({exc}). Prøv igjen.")
            continue
        if normalized:
            return normalized
        print("Stien kan ikkje vere tom. Prøv igjen.")


def _prompt_api_key(existing: str | None) -> str:
    if existing:
        keep = input(
            f"Det finst allereie ein API-nøkkel ({preview_key(existing)}). Vil du bruke denne? [Y/n]: "
        ).strip().lower()
        if keep in {"", "y", "yes"}:
            return existing
    while True:
        key = getpass.getpass("Lim inn OpenAI API-nøkkelen din: ").strip()
        if key:
            return key
        print("API-nøkkelen kan ikkje vere tom. Prøv igjen.")


def _confirm(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [Y/n]: ").strip().lower()
        if answer in {"", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Svar med y eller n.")


def main() -> int:
    print("Velkomen til oppsettsguiden for note-maker.\n")
    existing = parse_env_file(ENV_PATH)

    api_key = _prompt_api_key(existing.get("OPENAI_API_KEY"))
    input_dir = _prompt_path(
        "Mapper med presentasjonane du vil lese frå", existing.get("HOST_INPUT_PATH", INPUT_FALLBACK)
    )
    output_dir = _prompt_path(
        "Mapper der notata skal lagrast", existing.get("HOST_OUTPUT_PATH", OUTPUT_FALLBACK)
    )
    copy_dir_default = existing.get("HOST_COPY_PATH") or existing.get("HOST_OUTPUT_PATH") or COPY_FALLBACK
    copy_dir = _prompt_path(
        "Mapper der presentasjonane skal kopierast", copy_dir_default
    )

    print("\nSamandrag:")
    print(f"  OpenAI-API: {preview_key(api_key)}")
    print(f"  Inndata:     {input_dir}")
    print(f"  Notatmappe:  {output_dir}")
    print(f"  Kopimappe:   {copy_dir}")

    if not _confirm("Lagre og opprette eventuelle manglande mapper?"):
        print("Avbryt. Ingen endringar vart lagra.")
        return 0

    for folder in (input_dir, output_dir, copy_dir):
        path = Path(folder)
        if not path.exists():
            ensure_directory(folder)
            print(f"Oppretta mappe: {folder}")

    values = {
        "OPENAI_API_KEY": api_key,
        "HOST_INPUT_PATH": input_dir,
        "HOST_OUTPUT_PATH": output_dir,
        "HOST_COPY_PATH": copy_dir,
    }
    preserved_lines = collect_preserved_lines(ENV_PATH)
    write_env_file(values, preserved_lines, ENV_PATH)

    print("\nFerdig! Konfigurasjonen er lagra i .env.")
    print("Køyr ./run.sh for å byggje og starte appen med desse innstillingane.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
