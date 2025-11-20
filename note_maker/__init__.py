"""Core helpers and web server for note-maker."""

from .core import (
    AVAILABLE_MODELS,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    LANGUAGE_LABELS,
    LANGUAGE_OPTIONS,
    GenerationResult,
    copy_source_file,
    extract_text,
    extract_text_from_pdf,
    extract_text_from_pptx,
    generate_note_from_file,
    generate_note_from_text,
    save_note_text,
)

__all__ = [
    "AVAILABLE_MODELS",
    "DEFAULT_LANGUAGE",
    "DEFAULT_MODEL",
    "LANGUAGE_LABELS",
    "LANGUAGE_OPTIONS",
    "GenerationResult",
    "copy_source_file",
    "extract_text",
    "extract_text_from_pdf",
    "extract_text_from_pptx",
    "generate_note_from_file",
    "generate_note_from_text",
    "save_note_text",
]
