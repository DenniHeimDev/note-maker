from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from typing import Literal, Optional

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
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from note_maker.core import (
    AVAILABLE_MODELS,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    LANGUAGE_OPTIONS,
    GenerationResult,
    generate_note_from_file,
)

_ENV_CACHE: dict[str, str] = {}
_CONFIG_REQUIRED = True


def _reload_env_cache() -> None:
    global _ENV_CACHE, _CONFIG_REQUIRED
    _ENV_CACHE = parse_env_file(ENV_PATH)
    required_keys = ("OPENAI_API_KEY", "HOST_INPUT_PATH", "HOST_OUTPUT_PATH", "HOST_COPY_PATH")
    _CONFIG_REQUIRED = not _ENV_CACHE or any(not _ENV_CACHE.get(key) for key in required_keys)
    api_key = _ENV_CACHE.get("OPENAI_API_KEY")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key


def _config_values() -> dict:
    return {
        "inputPath": _ENV_CACHE.get("HOST_INPUT_PATH", INPUT_FALLBACK),
        "outputPath": _ENV_CACHE.get("HOST_OUTPUT_PATH", OUTPUT_FALLBACK),
        "copyPath": _ENV_CACHE.get("HOST_COPY_PATH", COPY_FALLBACK),
    }


def _config_summary() -> dict:
    values = _config_values()
    key = _ENV_CACHE.get("OPENAI_API_KEY")
    return {
        "needsSetup": _CONFIG_REQUIRED,
        "values": values,
        "hasKey": bool(key),
        "keyPreview": preview_key(key) if key else "",
    }


_reload_env_cache()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

HOST_INPUT_DIR = Path(os.environ.get("HOST_INPUT_DIR", BASE_DIR / "input")).expanduser()
HOST_OUTPUT_DIR = Path(os.environ.get("HOST_OUTPUT_DIR", BASE_DIR / "output")).expanduser()
HOST_COPY_DIR = Path(os.environ.get("HOST_COPY_DIR", HOST_OUTPUT_DIR / "copies")).expanduser()

for folder in (HOST_INPUT_DIR, HOST_OUTPUT_DIR, HOST_COPY_DIR):
    folder.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="note-maker web")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _bool_from_form(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "on", "yes"}


def _read_index() -> str:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return "<h1>note-maker</h1><p>Frontend manglar. Bygg static/.</p>"
    return index_path.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def read_index() -> str:
    return _read_index()


@app.get("/healthz")
def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/api/options")
def api_options() -> dict:
    config_info = _config_summary()
    return {
        "models": AVAILABLE_MODELS,
        "defaultModel": DEFAULT_MODEL,
        "languages": [
            {"key": key, "label": data["label"]} for key, data in LANGUAGE_OPTIONS.items()
        ],
        "defaultLanguage": DEFAULT_LANGUAGE,
        "paths": {
            "inputRoot": str(HOST_INPUT_DIR),
            "outputRoot": str(HOST_OUTPUT_DIR),
            "copyRoot": str(HOST_COPY_DIR),
        },
        "config": config_info,
    }


def _resolve_inside(base: Path, relative_path: str) -> Path:
    cleaned = Path(relative_path) if relative_path else Path(".")
    candidate = (base / cleaned).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ugyldig sti.") from exc
    return candidate


def _list_directory(base: Path, relative: str, include_files: bool) -> dict:
    directory = _resolve_inside(base, relative)
    base_resolved = base.resolve()
    entries = []
    for child in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if child.name.startswith("."):
            continue
        relative_child = str(child.resolve().relative_to(base_resolved))
        if child.is_dir():
            entries.append({"name": child.name, "path": relative_child, "type": "dir"})
        elif include_files:
            entries.append({"name": child.name, "path": relative_child, "type": "file"})
    current_rel = "" if directory.resolve() == base_resolved else str(directory.resolve().relative_to(base_resolved))
    parent_rel = ""
    if current_rel:
        parent_rel = str(Path(current_rel).parent)
        if parent_rel == ".":
            parent_rel = ""
    return {
        "currentPath": current_rel,
        "parentPath": parent_rel,
        "entries": entries,
    }


@app.get("/api/browse")
def api_browse(
    root: Literal["input", "output", "copy"],
    path: Optional[str] = Query(default="", description="Relative path inside the selected root"),
) -> dict:
    base = {
        "input": HOST_INPUT_DIR,
        "output": HOST_OUTPUT_DIR,
        "copy": HOST_COPY_DIR,
    }[root]
    include_files = root == "input"
    listing = _list_directory(base, path or "", include_files=include_files)
    return {
        "root": root,
        "base": str(base),
        "canSelectFiles": include_files,
        **listing,
    }


@app.post("/api/generate")
async def api_generate(
    file: UploadFile | None = File(default=None),
    model: str = Form(DEFAULT_MODEL),
    language: str = Form(DEFAULT_LANGUAGE),
    copy_source: str | bool | None = Form(False),
    existing_path: str = Form("", description="Relative path to an existing file under HOST_INPUT_DIR"),
    output_dir: str = Form("", description="Relative path under HOST_OUTPUT_DIR"),
    copy_dir: str = Form("", description="Relative path under HOST_COPY_DIR"),
) -> dict:
    if _CONFIG_REQUIRED:
        raise HTTPException(status_code=428, detail="Konfigurer .env før du genererer notat.")
    source_path: Optional[Path] = None
    original_filename: Optional[str] = None
    temp_path: Optional[Path] = None

    existing_path = existing_path.strip()
    if existing_path:
        candidate = _resolve_inside(HOST_INPUT_DIR, existing_path)
        if not candidate.exists() or not candidate.is_file():
            raise HTTPException(status_code=400, detail="Fila finst ikkje.")
        if candidate.suffix.lower() not in {".pdf", ".pptx"}:
            raise HTTPException(status_code=400, detail="Berre .pdf eller .pptx er støtta.")
        source_path = candidate
        original_filename = candidate.name
    else:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="Vel ei fil eller bruk eksisterande fil.")
        file_suffix = Path(file.filename).suffix.lower()
        if file_suffix not in {".pdf", ".pptx"}:
            raise HTTPException(status_code=400, detail="Berre .pdf eller .pptx er støtta.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = Path(tmp.name)
        source_path = temp_path
        original_filename = file.filename

    output_target = _resolve_inside(HOST_OUTPUT_DIR, output_dir.strip()) if output_dir.strip() else HOST_OUTPUT_DIR
    copy_target = _resolve_inside(HOST_COPY_DIR, copy_dir.strip()) if copy_dir.strip() else HOST_COPY_DIR
    copy_requested = _bool_from_form(copy_source)
    try:
        result: GenerationResult = generate_note_from_file(
            source_path,
            original_filename=original_filename,
            output_dir=output_target,
            model_name=model,
            language_key=language,
            copy_requested=copy_requested,
            copy_dir=copy_target if copy_requested else None,
        )
    except Exception as exc:  # broad: we want to surface user friendly errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if file:
            file.file.close()
        if temp_path:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    return {
        "noteName": result.note_path.name,
        "notePath": str(result.note_path),
        "noteText": result.note_text,
        "copiedPath": str(result.copied_path) if result.copied_path else None,
        "downloadUrl": f"/api/notes/{result.note_path.name}",
        "outputDir": str(output_target),
        "copyDir": str(copy_target if copy_requested else ""),
    }


@app.get("/api/notes/{note_name}")
def download_note(note_name: str) -> FileResponse:
    if "/" in note_name or "\\" in note_name or ".." in note_name:
        raise HTTPException(status_code=400, detail="Ugyldig filnamn.")
    note_path = (HOST_OUTPUT_DIR / note_name).resolve()
    try:
        note_path.relative_to(HOST_OUTPUT_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ugyldig filbane.") from exc
    if not note_path.exists():
        raise HTTPException(status_code=404, detail="Fann ikkje fila.")
    return FileResponse(note_path, filename=note_path.name, media_type="text/markdown")


class ConfigPayload(BaseModel):
    apiKey: Optional[str] = None
    inputPath: str
    outputPath: str
    copyPath: str


@app.get("/api/config")
def api_get_config() -> dict:
    return _config_summary()


@app.post("/api/config")
def api_save_config(payload: ConfigPayload) -> dict:
    existing = _config_values()
    try:
        input_path = normalize_path(payload.inputPath.strip() or existing["inputPath"])
        output_raw = payload.outputPath.strip()
        output_path = normalize_path(output_raw or existing["outputPath"])
        copy_input = payload.copyPath.strip()
        if copy_input:
            copy_path = normalize_path(copy_input)
        elif output_raw:
            copy_path = output_path
        else:
            copy_path = normalize_path(existing["copyPath"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Ugyldig sti: {exc}") from exc

    api_key_candidate = (payload.apiKey or "").strip()
    stored_key = _ENV_CACHE.get("OPENAI_API_KEY", "").strip()
    api_key = api_key_candidate or stored_key
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API-nøkkel må fyllast ut.")

    for folder in (input_path, output_path, copy_path):
        ensure_directory(folder)

    values = {
        "OPENAI_API_KEY": api_key,
        "HOST_INPUT_PATH": input_path,
        "HOST_OUTPUT_PATH": output_path,
        "HOST_COPY_PATH": copy_path,
    }
    preserved = collect_preserved_lines(ENV_PATH)
    write_env_file(values, preserved, ENV_PATH)
    os.environ["OPENAI_API_KEY"] = api_key
    _reload_env_cache()
    return {"status": "ok"}
