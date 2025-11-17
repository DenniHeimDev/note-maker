from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from note_maker.core import (
    AVAILABLE_MODELS,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    LANGUAGE_OPTIONS,
    GenerationResult,
    generate_note_from_file,
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

HOST_OUTPUT_DIR = Path(os.environ.get("HOST_OUTPUT_DIR", BASE_DIR / "output")).expanduser()
HOST_COPY_DIR = Path(os.environ.get("HOST_COPY_DIR", HOST_OUTPUT_DIR / "copies")).expanduser()

HOST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HOST_COPY_DIR.mkdir(parents=True, exist_ok=True)

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
    return {
        "models": AVAILABLE_MODELS,
        "defaultModel": DEFAULT_MODEL,
        "languages": [
            {"key": key, "label": data["label"]} for key, data in LANGUAGE_OPTIONS.items()
        ],
        "defaultLanguage": DEFAULT_LANGUAGE,
        "paths": {
            "output": str(HOST_OUTPUT_DIR),
            "copy": str(HOST_COPY_DIR),
        },
    }


@app.post("/api/generate")
async def api_generate(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
    language: str = Form(DEFAULT_LANGUAGE),
    copy_source: str | bool | None = Form(False),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Du må laste opp ei fil.")
    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in {".pdf", ".pptx"}:
        raise HTTPException(status_code=400, detail="Berre .pdf eller .pptx er støtta.")

    copy_requested = _bool_from_form(copy_source)
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = Path(tmp.name)
    try:
        result: GenerationResult = generate_note_from_file(
            temp_path,
            original_filename=file.filename,
            output_dir=HOST_OUTPUT_DIR,
            model_name=model,
            language_key=language,
            copy_requested=copy_requested,
            copy_dir=HOST_COPY_DIR if copy_requested else None,
        )
    except Exception as exc:  # broad: we want to surface user friendly errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        file.file.close()
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
