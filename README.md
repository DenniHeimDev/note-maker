# Note Maker

Note Maker is a local-first web app that turns PDF or PowerPoint presentations into structured study notes with the help of OpenAI's GPT models. Everything runs on your machine: the FastAPI backend processes uploads, the browser UI drives the workflow, and the only external call goes to OpenAI.

## Features
- Extracts raw text from `.pptx` and `.pdf` decks (tables included) before handing it to GPT.
- Ships with opinionated prompts for Nynorsk, Bokmål, and English plus a configurable model list (defaults to `gpt-5.1`).
- Copies the original presentation into an archive folder when requested so you can keep source material next to each note.
- Runs as a browser-based UI powered by FastAPI + vanilla JavaScript—no Tkinter/X11 requirements anymore.

## Requirements
- Python 3.10+ (needed for the setup helpers or if you run the app without Docker).
- Docker and Docker Compose (used by `run.sh` to build and run the FastAPI server).
- An OpenAI API key with access to the GPT models you want to target.

## Getting Started
1. **Configure environment** – Choose `python setup.py` (GUI helper) or `python setup_cli.py` (CLI) and follow the prompts.  
   Both helpers store your OpenAI key plus the host folders that should be mounted into `.env`.
2. **Start the container** – Run `./run.sh`. The script loads `.env`, exports `OPENAI_API_KEY`, ensures your input/output/copy folders exist, and launches `docker compose up --build`.
3. **Use the web UI** – Once Docker prints that the server is ready, open `http://localhost:8000` in your browser. Upload a PDF/PPTX, pick a model/language, decide whether to copy the original file, and click **Generate note**. The page shows live status plus download/copy buttons when GPT finishes.

## Configuration Reference
The application reads configuration exclusively from environment variables (which the setup helpers write into `.env`):

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
HOST_INPUT_PATH=/path/on/host/with/presentations
HOST_OUTPUT_PATH=/path/on/host/for/notes
HOST_COPY_PATH=/path/on/host/for/presentation-backups
```

- `HOST_OUTPUT_PATH` determines where generated Markdown notes land (and is where the UI fetches download links from).
- `HOST_COPY_PATH` is used when the “copy presentation” checkbox is selected; files are deduplicated automatically.

If you prefer to manage configuration manually, mirror the same keys in your own `.env` or exported shell variables before running `./run.sh`.

## Setup Helpers
- `python setup.py` launches a Tkinter assistant with masked API key entry, directory pickers, inline validation, and a “Test mapper” button that creates missing folders before saving `.env`.
- `python setup_cli.py` is the original terminal-based helper that asks the same questions if you prefer the keyboard-only flow.

Both helpers write identical `.env` files, so you can switch between them at any time.

## Running Without Docker
You can run the FastAPI server directly if you have Python and the dependencies installed locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=...
uvicorn note_maker.server:app --reload
```

Then visit `http://localhost:8000` just like when using Docker. Optional environment variables (`HOST_OUTPUT_DIR`, `HOST_COPY_DIR`) still control where generated files are stored.

## Notes on ChatGPT Usage
- The list of models lives in `note_maker/core.py` (`AVAILABLE_MODELS`). Add or remove names there if OpenAI rolls out new versions.
- Prompts for each supported language are defined in `LANGUAGE_OPTIONS`. Adjust them to change tone, formatting rules, or add more languages.
- The server never exposes your API key to the browser; only the backend calls OpenAI.

## Troubleshooting
- **“OPENAI_API_KEY is not set”** – Ensure `.env` exists or export the key in your shell before running `./run.sh`.
- **Upload errors** – Only `.pdf` and `.pptx` files are accepted. If your deck is huge, be patient: extraction happens before the request reaches GPT.
- **Permission errors / missing folders** – Double-check that the host paths in `.env` point to locations Docker Desktop/WSL can mount and that your user has read/write rights.

Feel free to extend the prompts, add languages, or build a richer frontend—everything is intentionally small so you can customize it quickly.
