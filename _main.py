#!/usr/bin/env python3
"""Entry point that launches the FastAPI server via uvicorn."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload_flag = os.environ.get("UVICORN_RELOAD", "").lower() in {"1", "true", "yes"}
    uvicorn.run("note_maker.server:app", host=host, port=port, reload=reload_flag)


if __name__ == "__main__":
    main()
