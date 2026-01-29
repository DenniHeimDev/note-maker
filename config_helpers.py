from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List


def get_user_config_dir() -> Path:
    """Return the user-specific configuration directory."""

    app_name = "note-maker"
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    config_dir = base / app_name
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


USER_CONFIG_DIR = get_user_config_dir()


def resolve_env_path() -> Path:
    """Resolve where note-maker should read/write its configuration.

    Precedence:
      1) NOTE_MAKER_ENV_PATH environment variable (explicit override)
      2) .env in the current working directory (repo/dev-friendly)
      3) User config dir (~/.config/note-maker/config.env)

    This makes Docker/dev setups use the repo-local .env by default, while
    packaged/native apps still get a per-user config file.
    """

    override = os.environ.get("NOTE_MAKER_ENV_PATH")
    if override:
        return Path(override).expanduser()

    cwd = Path.cwd()
    cwd_env = cwd / ".env"

    in_docker = Path("/.dockerenv").exists()

    # In a repo/dev environment we want to use a local .env even if it doesn't
    # exist yet (setup scripts should create it). Inside Docker containers we
    # avoid defaulting to /app/.env unless it already exists.
    if cwd_env.exists() or ((cwd / "docker-compose.yml").exists() and not in_docker):
        return cwd_env

    return USER_CONFIG_DIR / "config.env"


ENV_PATH = resolve_env_path()

MANAGED_KEYS = {
    "OPENAI_API_KEY",
    "HOST_INPUT_PATH",
    "HOST_OUTPUT_PATH",
    "HOST_COPY_PATH",
}


def get_system_defaults() -> Dict[str, str]:
    """Detect standard system paths for the current OS."""

    home = Path.home()

    docs = home / "Documents"
    downloads = home / "Downloads"
    desktop = home / "Desktop"

    # Fallback if they don't exist (e.g. server environments)
    if not docs.exists():
        docs = home
    if not downloads.exists():
        downloads = home

    return {
        "home": str(home),
        "documents": str(docs),
        "downloads": str(downloads),
        "desktop": str(desktop) if desktop.exists() else str(home),
    }


_defaults = get_system_defaults()
INPUT_FALLBACK = _defaults["downloads"]
OUTPUT_FALLBACK = _defaults["documents"]
COPY_FALLBACK = _defaults["documents"]


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
            # Backwards compatibility: allow files containing only the key.
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
    lines = ["# note-maker configuration", f"# Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}"]
    for key in ("OPENAI_API_KEY", "HOST_INPUT_PATH", "HOST_OUTPUT_PATH", "HOST_COPY_PATH"):
        lines.append(f"{key}=\"{values[key]}\"")

    preserved = list(preserved_lines)
    if preserved:
        lines.append("")
        lines.append("# Other values preserved from before")
        lines.extend(preserved)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_directory(path_str: str) -> None:
    Path(path_str).mkdir(parents=True, exist_ok=True)


def preview_key(key: str) -> str:
    if len(key) <= 8:
        return key
    return f"{key[:4]}...{key[-4:]}"
