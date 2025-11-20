# Note Maker

Note Maker is a local-first web app that turns PDF or PowerPoint presentations into structured study notes with the help of OpenAI's GPT models. Everything runs on your machine: the FastAPI backend processes uploads, the browser UI drives the workflow, and the only external call goes to OpenAI.

## Features
- **Local-First**: Runs entirely on your machine using Docker.
- **Format Support**: Extracts text from `.pptx` and `.pdf` decks (tables included).
- **Language Options**: Pre-configured prompts for Nynorsk, Bokmål, and English.
- **Archive**: Optionally copies the original presentation to a backup folder.
- **Browser UI**: Modern web interface to manage files and configuration.
- **Config Editor**: Built-in `.env` editor in the browser.

> [!NOTE]
> **Language Support**: The application documentation and code comments are in English, but the user interface (UI) and user-facing messages are in **Norwegian** to support the primary user base.

## Project Structure

```
note-maker/
├── note_maker/           # Core application logic
│   ├── core.py           # Text extraction and OpenAI integration
│   └── server.py         # FastAPI backend and API endpoints
├── static/               # Frontend assets
│   ├── index.html        # Main UI structure
│   ├── app.js            # Frontend logic
│   └── styles.css        # Styling
├── config_helpers.py     # Configuration and .env management
├── run.sh                # Entry point script (Docker Compose wrapper)
├── setup.py              # GUI setup assistant
├── setup_cli.py          # CLI setup assistant
├── docker-compose.yml    # Docker services configuration
└── requirements.txt      # Python dependencies
```

## Requirements
- **Docker** and **Docker Compose**: Required to run the application via `run.sh`.
- **Python 3.10+**: Required only if you want to run the setup helpers (`setup.py`/`setup_cli.py`) or run the app without Docker.
- **OpenAI API Key**: Access to GPT models (e.g., `gpt-4o`, `gpt-5`).

## Getting Started

1.  **Configure Environment**
    -   **GUI**: Run `python setup.py` for a graphical assistant.
    -   **CLI**: Run `python setup_cli.py` for a terminal-based setup.
    -   **Browser**: You can also skip this and configure everything in the browser on first launch.

2.  **Start the Application**
    Run the start script:
    ```bash
    ./run.sh
    ```
    This script ensures your environment is set up and launches the container.

3.  **Use the Web UI**
    Open `http://localhost:8000` in your browser.
    -   **Upload**: Drag & drop a PDF/PPTX file.
    -   **Select**: Pick an existing file from your mounted input folder.
    -   **Generate**: Choose your model and language, then click **Generate note**.

## Configuration

The application uses a `.env` file for configuration. You can edit this file directly, use the setup scripts, or use the "Edit configuration" button in the web UI.

| Variable | Description |
| :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key. |
| `HOST_INPUT_PATH` | Local folder containing presentations to read. |
| `HOST_OUTPUT_PATH` | Local folder where generated notes will be saved. |
| `HOST_COPY_PATH` | Local folder for backing up presentations (optional). |

## Running Without Docker

If you prefer to run the FastAPI server directly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn note_maker.server:app --reload
```

Visit `http://localhost:8000` to use the app.

## Troubleshooting

-   **"OPENAI_API_KEY is not set"**: Ensure `.env` exists or the key is exported in your shell.
-   **Upload errors**: Only `.pdf` and `.pptx` files are supported. Large files may take time to extract.
-   **Permission errors**: Ensure Docker has permission to mount the host directories specified in `.env`.

## Building Native App

## Building Native App

To run Note Maker as a standalone desktop app (without Docker), follow these steps:

1.  **Install Python**: Ensure you have Python 3.10+ installed.
2.  **Run the Build Script**:
    ```bash
    python build_native.py
    ```
    This script will automatically install dependencies and build the application.

3.  **Launch**:
    -   **Windows**: Open `dist\note-maker\note-maker.exe`
    -   **macOS**: Open `dist/note-maker.app`
    -   **Linux**: Run `dist/note-maker/note-maker`

> [!NOTE]
> On Linux, you may need system dependencies for the GUI window (GTK/Qt).
> On Ubuntu/Debian: `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`

## Automated Builds (GitHub Actions)

Since PyInstaller builds are specific to the OS they run on (you can't build a Windows `.exe` on Linux), this project includes a GitHub Actions workflow to build for all platforms automatically.

1.  Push your code to GitHub.
2.  Go to the **Actions** tab in your repository.
3.  Click on the latest **Build Native App** run.
4.  Scroll down to **Artifacts** and download the version for your OS (`note-maker-Windows`, `note-maker-macOS`, etc.).
