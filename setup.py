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
from typing import Dict, Iterable, List


ENV_PATH = Path(".env")
MANAGED_KEYS = {
    "OPENAI_API_KEY",
    "HOST_INPUT_PATH",
    "HOST_OUTPUT_PATH",
    "HOST_COPY_PATH",
}

# Fallback paths mimic the previous hard coded defaults so existing workflows
# continue to behave as expected if the user simply accepts every prompt.
INPUT_FALLBACK = "/mnt/c/Users/denni/Downloads"
OUTPUT_FALLBACK = (
    "/mnt/c/Users/denni/Telia Sky/Obsidian/DenniHeim's Vault/1. Projects/FORKURS"
)
COPY_FALLBACK = OUTPUT_FALLBACK


def _parse_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    result: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
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
        result[name] = value
    return result


def _normalize_path(candidate: str) -> str:
    expanded = Path(candidate).expanduser()
    # resolve(strict=False) keeps whatever the user typed even if it does not yet
    # exist, but still removes ".." and redundant separators.
    resolved = expanded.resolve(strict=False)
    return str(resolved)


def _prompt_path(message: str, default_value: str) -> str:
    while True:
        prompt = f"{message} [{default_value}]: "
        user_input = input(prompt).strip()
        if not user_input:
            user_input = default_value
        try:
            normalized = _normalize_path(user_input)
        except Exception as exc:  # pragma: no cover - interactive helper
            print(f"Kunne ikkje tolke stien ({exc}). Prøv igjen.")
            continue
        if normalized:
            return normalized
        print("Stien kan ikkje vere tom. Prøv igjen.")


def _prompt_api_key(existing: str | None) -> str:
    if existing:
        preview = f"{existing[:4]}...{existing[-4:]}" if len(existing) > 8 else existing
        keep = input(
            f"Det finst allereie ein API-nøkkel ({preview}). Vil du bruke denne? [Y/n]: "
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


def _collect_preserved_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    preserved: List[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            preserved.append(raw_line)
            continue
        if "=" not in stripped:
            preserved.append(raw_line)
            continue
        name = stripped.split("=", 1)[0].strip()
        if name in MANAGED_KEYS:
            continue
        preserved.append(raw_line)
    return preserved


def _write_env_file(values: Dict[str, str], preserved_lines: Iterable[str]) -> None:
    lines = ["# note-maker configuration", f"# Sist oppdatert: {datetime.now():%Y-%m-%d %H:%M:%S}"]
    for key in ("OPENAI_API_KEY", "HOST_INPUT_PATH", "HOST_OUTPUT_PATH", "HOST_COPY_PATH"):
        lines.append(f"{key}={values[key]}")
    preserved = list(preserved_lines)
    if preserved:
        lines.append("")
        lines.append("# Andre verdiar bevart frå før")
        lines.extend(preserved)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    print("Velkomen til oppsettsguiden for note-maker.\n")
    existing = _parse_env_file(ENV_PATH)

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
    print(f"  OpenAI-API: {api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else f"  OpenAI-API: {api_key}")
    print(f"  Inndata:     {input_dir}")
    print(f"  Notatmappe:  {output_dir}")
    print(f"  Kopimappe:   {copy_dir}")

    if not _confirm("Lagre og opprette eventuelle manglande mapper?"):
        print("Avbryt. Ingen endringar vart lagra.")
        return 0

    for folder in (input_dir, output_dir, copy_dir):
        path = Path(folder)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Oppretta mappe: {folder}")

    values = {
        "OPENAI_API_KEY": api_key,
        "HOST_INPUT_PATH": input_dir,
        "HOST_OUTPUT_PATH": output_dir,
        "HOST_COPY_PATH": copy_dir,
    }
    preserved_lines = _collect_preserved_lines(ENV_PATH)
    _write_env_file(values, preserved_lines)

    print("\nFerdig! Konfigurasjonen er lagra i .env.")
    print("Køyr ./run.sh for å byggje og starte appen med desse innstillingane.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
