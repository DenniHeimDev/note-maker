from __future__ import annotations

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

INPUT_FALLBACK = "/mnt/c/Users/denni/Downloads"
OUTPUT_FALLBACK = (
    "/mnt/c/Users/denni/Telia Sky/Obsidian/DenniHeim's Vault/1. Projects/FORKURS"
)
COPY_FALLBACK = OUTPUT_FALLBACK


def parse_env_file(path: Path = ENV_PATH) -> Dict[str, str]:
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


def normalize_path(candidate: str) -> str:
    expanded = Path(candidate).expanduser()
    resolved = expanded.resolve(strict=False)
    return str(resolved)


def collect_preserved_lines(path: Path = ENV_PATH) -> List[str]:
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


def write_env_file(
    values: Dict[str, str],
    preserved_lines: Iterable[str],
    path: Path = ENV_PATH,
) -> None:
    lines = ["# note-maker configuration", f"# Sist oppdatert: {datetime.now():%Y-%m-%d %H:%M:%S}"]
    for key in ("OPENAI_API_KEY", "HOST_INPUT_PATH", "HOST_OUTPUT_PATH", "HOST_COPY_PATH"):
        lines.append(f"{key}={values[key]}")
    preserved = list(preserved_lines)
    if preserved:
        lines.append("")
        lines.append("# Andre verdiar bevart frå før")
        lines.extend(preserved)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_directory(path_str: str) -> None:
    Path(path_str).mkdir(parents=True, exist_ok=True)


def preview_key(key: str) -> str:
    if len(key) <= 8:
        return key
    return f"{key[:4]}...{key[-4:]}"
