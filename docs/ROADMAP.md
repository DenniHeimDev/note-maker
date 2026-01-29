# Note Maker – Development Plan / Roadmap

This roadmap is meant to be practical: what to build next, why, and in what order.

## 0) Baseline: keep the current workflow solid

**Goal:** “It works every time” for PDF/PPTX → note generation.

- Add lightweight smoke tests (CI):
  - start the FastAPI app
  - hit `/healthz`, `/api/options`
  - run a minimal “generate” flow with a tiny fixture file (or mocked OpenAI)
- Add a `Makefile` or `scripts/` helpers for common tasks (lint, run, build)
- Add structured logging (request id, duration, selected model/language)

## 1) UX improvements (low effort, high impact)

- Better progress feedback during extraction + generation ("Extracting…", "Calling model…")
- Show model + language in the result header
- Persist last-used settings in browser localStorage
- Provide a “Regenerate” button that reuses the same input settings

## 2) Extraction quality (make input better)

**PPTX**
- Preserve basic slide structure (titles vs body) to improve prompts
- Capture speaker notes (optional toggle)

**PDF**
- Optional OCR mode for scanned PDFs (e.g., `pytesseract`) with a clear warning about speed
- Improve table extraction strategy (currently “text” only)

## 3) Prompting + output formats

- Add a “style preset” dropdown (lecture notes, flashcards, summary, Q&A)
- Add “citations / source section” option (list headings/sections extracted)
- Add “output formats”:
  - Markdown (current)
  - Obsidian-friendly template (frontmatter + tags)
  - Anki CSV (basic)

## 4) Cost / speed controls

- Add chunking + map-reduce strategy for very large files
- Add token counting / estimated cost before generation
- Add caching keyed by (file hash, model, language, preset)

## 5) Local-first + privacy

- Document exactly what is sent to OpenAI (extracted text only)
- Optional redaction filters (emails, phone numbers) before sending
- Add an “offline mode” placeholder that disables generation cleanly

## 6) Packaging + distribution

- Confirm Windows/macOS/Linux packaging workflows (PyInstaller) and document known issues
- Add versioning (semver) and a changelog

## Suggested milestone breakdown

- **v0.1.1**: CI smoke tests, docs cleanup, config consistency
- **v0.2**: UX improvements + presets
- **v0.3**: Better extraction (speaker notes, optional OCR)
- **v0.4**: Chunking/caching + cost estimate

## Notes for contributors

If you add new environment variables, document them in README and keep them compatible with Docker usage (values may come from a `.env` file *or* the process environment).
