# Note Maker

Note Maker is a small desktop utility that turns PDF or PowerPoint presentations into structured study notes with the help of OpenAI's GPT models.  
The interface is written in Tkinter, packaged in Docker, and—per the creator's request—this app (and its documentation) was made using ChatGPT.

## Features
- Extracts raw text from `.pptx` and `.pdf` presentations and keeps simple table formatting.
- Sends the extracted content to configurable OpenAI GPT models (defaults to `gpt-5.1`) to produce high quality notes.
- Ships with writing templates for Nynorsk, Bokmål, and English so each language keeps tone and terminology.
- Optional one-click copy of the source presentation into the export folder (handy for archiving).
- Simple GUI that runs locally but mounts folders from the host OS, so nothing ever leaves your machine except the API call to OpenAI.

## Requirements
- Python 3.10+ (only needed for the `setup.py` helper or for running the app without Docker).
- Docker and Docker Compose (used by `run.sh` to build and run the GUI container).
- An OpenAI API key with access to the GPT models you want to target.
- X server access if you start the GUI from WSL or a headless/Linux environment (`DISPLAY` is set to `:0` by `run.sh` when missing).

## Getting Started
1. **Configure environment** – Run `python setup.py` and follow the prompts.  
   The helper stores your OpenAI key plus the host folders that should be mounted into `.env` (existing content is preserved).
2. **Start the container** – Execute `./run.sh`. The script:
   - Pulls in configuration from `.env` (or `.env`-like files) and exports `OPENAI_API_KEY`, `HOST_INPUT_PATH`, `HOST_OUTPUT_PATH`, and `HOST_COPY_PATH`.
   - Creates the host folders if they do not exist yet.
   - Launches `docker compose up --build` so the GUI runs inside the container.
3. **Use the GUI** – Once the Tkinter window shows up:
   - Pick a PowerPoint or PDF file.
   - Choose the output folder (and optionally a folder that should receive a copy of the original file).
   - Select one of the available GPT models or language presets.
   - Click “Generer nynorsk notat” to kick off the threaded workflow that extracts text, calls the ChatGPT model, and writes the Markdown note.

The generated notes will be saved as `<original_file>_<language_suffix>.md` in your chosen output directory.

## Configuration Reference
The application reads configuration exclusively from environment variables (which `setup.py` writes into `.env`):

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
HOST_INPUT_PATH=/path/on/host/with/presentations
HOST_OUTPUT_PATH=/path/on/host/for/notes
HOST_COPY_PATH=/path/on/host/for/presentation-backups
```

- `HOST_INPUT_PATH` is where the file picker starts when you click “Bla gjennom”.
- `HOST_OUTPUT_PATH` becomes the initial save location for generated notes.
- `HOST_COPY_PATH` is used when the “Kopier presentasjonen” checkbox is enabled; the app keeps incrementing filenames to avoid overwriting.

If you prefer to manage the file manually, mirror the same keys in your own `.env` or exported shell variables before running `./run.sh`.

## Running Without Docker
The GUI code lives in `_main.py`. If you would rather run it directly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=...
python _main.py
```

Optional environment variables (`HOST_INPUT_DIR`, `HOST_OUTPUT_DIR`, `HOST_COPY_DIR`) can still be set to seed the default folders when the Tkinter dialog opens.

## Notes on ChatGPT Usage
- The available models live in `_main.py` in the `AVAILABLE_MODELS` list; add/remove names there if OpenAI updates offerings.
- Each language option in `LANGUAGE_OPTIONS` defines both the system prompt and the user template, allowing you to fine-tune how ChatGPT crafts the final note.
- Because the app relies on ChatGPT responses, make sure your API usage complies with your organization's privacy requirements.

## Troubleshooting
- **API errors** – Confirm `OPENAI_API_KEY` is exported inside the Docker container (the status label in the GUI shows a ✓/✗ indicator).  
- **Missing fonts/UI issues** – Tkinter needs access to system fonts via the container. If the window fails to open on Linux/WSL, ensure `xhost +local:` (or similar) allows Docker to use your X server.
- **Large PDFs** – PyMuPDF reads the entire document into memory. Extremely large decks may take a while; progress is logged in the “Status og logg” panel.

Feel free to extend the prompts, add new languages, or integrate other GPT tools—the project was intentionally structured to make those tweaks straightforward.
