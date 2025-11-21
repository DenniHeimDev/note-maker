from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

import sys

def get_user_config_dir() -> Path:
    """Return the user-specific configuration directory."""
    app_name = "note-maker"
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        # Linux / Unix
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    
    config_dir = base / app_name
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

USER_CONFIG_DIR = get_user_config_dir()
ENV_PATH = USER_CONFIG_DIR / "config.env"

MANAGED_KEYS = {
    "OPENAI_API_KEY",
    "HOST_INPUT_PATH",
    "HOST_OUTPUT_PATH",
    "HOST_COPY_PATH",
}

def get_system_defaults() -> Dict[str, str]:
    """Detect standard system paths for the current OS."""
    home = Path.home()
    
    # Common standard paths
    docs = home / "Documents"
    downloads = home / "Downloads"
    desktop = home / "Desktop"
    
    # Fallback if they don't exist (e.g. server environment)
    if not docs.exists(): docs = home
    if not downloads.exists(): downloads = home
    
    return {
        "home": str(home),
        "documents": str(docs),
        "downloads": str(downloads),
        "desktop": str(desktop) if desktop.exists() else str(home)
    }

# Initialize defaults dynamically
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
        lines.append(f"{key}={values[key]}")
    preserved = list(preserved_lines)
    if preserved:
        lines.append("")
        lines.append("# Other values preserved from before")
        lines.extend(preserved)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_directory(path_str: str) -> None:
    Path(path_str).mkdir(parents=True, exist_ok=True)


def preview_key(key: str) -> str:
    if len(key) <= 8:
        return key
    return f"{key[:4]}...{key[-4:]}"
