import os
import sys
import threading
import webview
import uvicorn
from note_maker.server import app

# Ensure we can find the note_maker package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_server():
    # Run the server on a specific port
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def main():
    # Start the FastAPI server in a separate thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # Create a native window pointing to the server
    webview.create_window(
        'Note Maker',
        'http://127.0.0.1:8000',
        width=1024,
        height=768,
        resizable=True
    )
    
    # Start the GUI loop
    webview.start()

if __name__ == '__main__':
    main()
