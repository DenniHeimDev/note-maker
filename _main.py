#!/usr/bin/env python3
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import fitz  # PyMuPDF
from dotenv import load_dotenv
from pptx import Presentation
from openai import OpenAI

MODEL_NAME = "gpt-5"
SYSTEM_PROMPT = (
    "Du er ein fagleg dyktig skribent som skriv klart og presist på nynorsk.\n"
    "Du får tekst frå ei fagleg presentasjon (PowerPoint eller PDF) og skal lage\n"
    "eit strukturert notat på nynorsk. Behald fagterminologi, bruk overskrifter\n"
    "og underoverskrifter der det passar, og skriv i ein stil som eignar seg\n"
    "som førebuing til undervisning eller eksamen."
)
USER_PROMPT_TEMPLATE = (
    "Her er innhaldet frå presentasjonen. Lag eit strukturert notat på nynorsk\n"
    "som oppsummerer og forklarer innhaldet. Du skal ikkje referere til \"slides\"\n"
    "eller \"bilete\", berre skrive eit samanhengande notat.\n\n"
    "=== START AV INPUT ===\n"
    "{tekst_her}\n"
    "=== SLUTT AV INPUT ==="
)

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def extract_text_from_pptx(file_path: str) -> str:
    presentation = Presentation(file_path)
    sections = []
    for slide in presentation.slides:
        slide_parts = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                for paragraph in shape.text_frame.paragraphs:
                    text = "".join(run.text for run in paragraph.runs).strip()
                    if text:
                        slide_parts.append(text)
            elif getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        slide_parts.append(" | ".join(cells))
        if slide_parts:
            sections.append("\n".join(slide_parts))
    return "\n\n".join(sections)


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    pages = []
    try:
        for page in doc:
            page_text = page.get_text("text").strip()
            if page_text:
                pages.append(page_text)
    finally:
        doc.close()
    return "\n\n".join(pages)


def extract_text(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pptx":
        return extract_text_from_pptx(file_path)
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    raise ValueError("Ukjend filtype. Vel ei .pptx- eller .pdf-fil.")


def generate_note_from_text(text: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("Miljøvariabelen OPENAI_API_KEY er ikkje sett.")
    if not text.strip():
        raise ValueError("Fann ikkje tekst i den valde fila.")
    user_prompt = USER_PROMPT_TEMPLATE.format(tekst_her=text.strip())
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    note = response.choices[0].message.content
    if not note:
        raise RuntimeError("Modellen returnerte ikkje noko innhald.")
    return note.strip()


def save_note_text(note_text: str, output_dir: str, source_file: str) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_stem = Path(source_file).stem
    note_file = output_path / f"{file_stem}_notat_nynorsk.md"
    with note_file.open("w", encoding="utf-8") as handle:
        handle.write(note_text)
    return note_file


def copy_source_file(source_file: str, output_dir: str) -> Path:
    destination = Path(output_dir) / Path(source_file).name
    shutil.copy2(source_file, destination)
    return destination


class NoteMakerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Nynorsk notatgenerator for presentasjonar")
        self.root.geometry("900x650")

        self.input_mount = Path(os.environ.get("HOST_INPUT_DIR", "/host/input"))
        self.output_mount = Path(os.environ.get("HOST_OUTPUT_DIR", "/host/output"))
        self.copy_mount = Path(os.environ.get("HOST_COPY_DIR", "/host/copies"))
        self.file_path = tk.StringVar()
        default_output = str(
            self.output_mount if self.output_mount.exists() else Path.home()
        )
        self.output_dir = tk.StringVar(value=default_output)
        self.copy_source = tk.BooleanVar(value=False)

        self._build_layout()
        self.update_api_key_status()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        status_frame = ttk.LabelFrame(self.root, text="OpenAI API-nøkkel")
        status_frame.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.api_status_label = tk.Label(status_frame, anchor="w", font=("TkDefaultFont", 10, "bold"))
        self.api_status_label.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        file_frame = ttk.LabelFrame(self.root, text="1. Vel presentasjonsfil")
        file_frame.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="Fil:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path, state="readonly")
        self.file_entry.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ttk.Button(file_frame, text="Bla gjennom", command=self.choose_file).grid(
            row=0, column=2, padx=6, pady=6
        )

        output_frame = ttk.LabelFrame(self.root, text="2. Vel lagringsmappe")
        output_frame.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Mappe:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir, state="readonly")
        self.output_entry.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ttk.Button(output_frame, text="Vel mappe", command=self.choose_output_dir).grid(
            row=0, column=2, padx=6, pady=6
        )

        ttk.Checkbutton(
            output_frame,
            text="Kopier presentasjonen til lagringsmappa",
            variable=self.copy_source,
        ).grid(row=1, column=0, columnspan=3, padx=6, pady=(0, 6), sticky="w")

        log_frame = ttk.LabelFrame(self.root, text="Status og logg")
        log_frame.grid(row=3, column=0, padx=12, pady=6, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_widget = scrolledtext.ScrolledText(
            log_frame, state="disabled", wrap="word", height=15
        )
        self.log_widget.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.process_button = ttk.Button(
            self.root, text="3. Generer nynorsk notat", command=self.start_processing
        )
        self.process_button.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="ew")

    def update_api_key_status(self) -> None:
        has_key = bool(OPENAI_API_KEY)
        if has_key:
            symbol = "✓"
            message = "API-nøkkel funnen"
            color = "green"
        else:
            symbol = "✗"
            message = "API-nøkkel manglar"
            color = "red"
        self.api_status_label.config(text=f"{symbol} {message}", foreground=color)

    def choose_file(self) -> None:
        filetypes = [
            ("Presentasjonar (*.pptx, *.pdf)", "*.pptx *.pdf"),
            ("PowerPoint (*.pptx)", "*.pptx"),
            ("PDF (*.pdf)", "*.pdf"),
        ]
        selected = filedialog.askopenfilename(
            title="Vel ei presentasjonsfil",
            filetypes=filetypes,
            initialdir=self._initial_dir(self.input_mount),
        )
        if selected:
            self.file_path.set(selected)
            self.log_message(f"Valde fil: {selected}")

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Vel lagringsmappe",
            initialdir=self._initial_dir(self.output_mount),
        )
        if selected:
            self.output_dir.set(selected)
            self.log_message(f"Valde lagringsmappe: {selected}")

    def start_processing(self) -> None:
        file_path = self.file_path.get()
        output_dir = self.output_dir.get()

        if not file_path:
            messagebox.showwarning("Manglar fil", "Vel ei presentasjonsfil før du held fram.")
            return
        if not Path(file_path).exists():
            messagebox.showerror("Fil finst ikkje", "Den valde fila vart ikkje funnen.")
            return
        copy_dir = str(self.copy_mount) if self.copy_mount.exists() else output_dir

        if not output_dir:
            messagebox.showwarning("Manglar mappe", "Vel lagringsmappe før du held fram.")
            return

        self.set_processing_state(True)
        self.log_message("Startar generering av notat ...")
        thread = threading.Thread(
            target=self._process_workflow,
            args=(file_path, output_dir, copy_dir, self.copy_source.get()),
            daemon=True,
        )
        thread.start()

    def set_processing_state(self, is_processing: bool) -> None:
        new_state = "disabled" if is_processing else "normal"
        self.process_button.config(state=new_state)

    def _process_workflow(
        self, file_path: str, output_dir: str, copy_dir: str, copy_requested: bool
    ) -> None:
        try:
            self.log_message("Hentar tekst frå fila ...")
            extracted_text = extract_text(file_path)
            self.log_message("Tekst ekstrahert. Sender til språkmodellen ...")
            note_text = generate_note_from_text(extracted_text)
            note_path = save_note_text(note_text, output_dir, file_path)
            self.log_message(f"Notat lagra som: {note_path}")
            copied_path = None
            if copy_requested:
                self.log_message("Kopierer presentasjonen til eksportmappa ...")
                copied_path = copy_source_file(file_path, copy_dir)
                self.log_message(f"Kopierte presentasjonen til {copied_path}")

            def success_message() -> None:
                message = f"Ferdig! Notatet er lagra som:\n{note_path}"
                if copied_path:
                    message += f"\nPresentasjonen vart kopiert til:\n{copied_path}"
                messagebox.showinfo("Ferdig", message)

            self.root.after(0, success_message)
        except Exception as exc:
            self.log_message(f"Feil: {exc}")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Feil under generering",
                    f"Arbeidsflyten stoppa på grunn av ein feil:\n{exc}",
                ),
            )
        finally:
            self.root.after(0, lambda: self.set_processing_state(False))

    def log_message(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.root.after(0, lambda: self._append_log(f"[{timestamp}] {message}"))

    def _initial_dir(self, mount_path: Path) -> str:
        if mount_path.exists():
            return str(mount_path)
        return os.getcwd()
    def _append_log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.configure(state="disabled")
        self.log_widget.see(tk.END)


def main() -> None:
    root = tk.Tk()
    NoteMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
