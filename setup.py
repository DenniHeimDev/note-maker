#!/usr/bin/env python3
"""Graphical setup assistant for note-maker."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

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


class SetupApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("note-maker oppsett")
        self.root.geometry("520x420")

        existing = parse_env_file(ENV_PATH)

        self.api_key = tk.StringVar(value=existing.get("OPENAI_API_KEY", ""))
        self.input_dir = tk.StringVar(value=existing.get("HOST_INPUT_PATH", INPUT_FALLBACK))
        self.output_dir = tk.StringVar(value=existing.get("HOST_OUTPUT_PATH", OUTPUT_FALLBACK))
        copy_default = existing.get("HOST_COPY_PATH") or existing.get("HOST_OUTPUT_PATH") or COPY_FALLBACK
        self.copy_dir = tk.StringVar(value=copy_default)
        self.status_var = tk.StringVar()
        self.message_var = tk.StringVar()

        self._build_layout()
        self._update_status(existing)
        self._validate_form()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        status_frame = ttk.LabelFrame(container, text="Gjeldande status")
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        status_frame.columnconfigure(0, weight=1)

        ttk.Label(status_frame, textvariable=self.status_var, foreground="#0a7b34").grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )

        form = ttk.Frame(container)
        form.grid(row=1, column=0, columnspan=2, sticky="nsew")
        for idx in range(3):
            form.columnconfigure(idx, weight=1 if idx == 1 else 0)

        ttk.Label(form, text="OpenAI API-nøkkel:").grid(row=0, column=0, sticky="w")
        api_entry = ttk.Entry(form, textvariable=self.api_key, show="•")
        api_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(form, text="Vis", command=lambda: self._toggle_secret(api_entry)).grid(row=0, column=2, padx=(0, 0))

        self._add_path_field(form, "Inndata-mappe:", self.input_dir, 1)
        self._add_path_field(form, "Notat-mappe:", self.output_dir, 2)
        self._add_path_field(form, "Kopi-mappe:", self.copy_dir, 3)

        self.message_label = ttk.Label(
            container, textvariable=self.message_var, foreground="#b45309", wraplength=480
        )
        self.message_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

        button_frame = ttk.Frame(container)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Test mapper", command=self._test_directories).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        self.save_button = ttk.Button(button_frame, text="Lagre konfigurasjon", command=self._save_configuration)
        self.save_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        for var in (self.api_key, self.input_dir, self.output_dir, self.copy_dir):
            var.trace_add("write", lambda *_: self._validate_form())

    def _add_path_field(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(12 if row == 1 else 8, 0))
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=(8, 8), pady=(12 if row == 1 else 8, 0))
        ttk.Button(parent, text="Bla gjennom", command=lambda: self._choose_folder(variable)).grid(
            row=row, column=2, pady=(12 if row == 1 else 8, 0)
        )

    def _toggle_secret(self, entry: ttk.Entry) -> None:
        new_show = "" if entry.cget("show") else "•"
        entry.config(show=new_show)

    def _choose_folder(self, target_var: tk.StringVar) -> None:
        initial = target_var.get().strip() or str(Path.home())
        selected = filedialog.askdirectory(title="Vel mappe", initialdir=initial)
        if selected:
            try:
                target_var.set(normalize_path(selected))
            except Exception as exc:
                messagebox.showerror("Ugyldig sti", f"Kunne ikkje bruke stien:\n{exc}")

    def _validate_form(self) -> None:
        errors = []
        if not self.api_key.get().strip():
            errors.append("Lim inn OpenAI API-nøkkelen din.")
        for label, var in (
            ("inndata-mappe", self.input_dir),
            ("notat-mappe", self.output_dir),
            ("kopi-mappe", self.copy_dir),
        ):
            if not var.get().strip():
                errors.append(f"Vel {label}.")
        if errors:
            self.message_var.set(" • ".join(errors))
            self.save_button.config(state="disabled")
        else:
            self.message_var.set("Alt klart – trykk «Lagre konfigurasjon».")
            self.save_button.config(state="normal")

    def _test_directories(self) -> None:
        paths = [self.input_dir.get().strip(), self.output_dir.get().strip(), self.copy_dir.get().strip()]
        missing = [p for p in paths if not p]
        if missing:
            messagebox.showwarning("Manglar verdiar", "Fyll inn alle mapper før du testar.")
            return
        try:
            for path in paths:
                ensure_directory(path)
            messagebox.showinfo("Suksess", "Mapper er tilgjengelege og klare.")
        except Exception as exc:
            messagebox.showerror("Feil ved testing", f"Kunne ikkje opprette/finne mapper:\n{exc}")

    def _save_configuration(self) -> None:
        self._validate_form()
        if self.save_button.cget("state") == "disabled":
            return
        input_dir = normalize_path(self.input_dir.get().strip())
        output_dir = normalize_path(self.output_dir.get().strip())
        copy_dir = normalize_path(self.copy_dir.get().strip())
        values = {
            "OPENAI_API_KEY": self.api_key.get().strip(),
            "HOST_INPUT_PATH": input_dir,
            "HOST_OUTPUT_PATH": output_dir,
            "HOST_COPY_PATH": copy_dir,
        }
        try:
            for folder in (input_dir, output_dir, copy_dir):
                ensure_directory(folder)
            preserved = collect_preserved_lines(ENV_PATH)
            write_env_file(values, preserved, ENV_PATH)
        except Exception as exc:
            messagebox.showerror("Feil ved lagring", f"Kunne ikkje lagre .env:\n{exc}")
            return
        self._update_status(values)
        messagebox.showinfo(
            "Konfig lagra",
            (
                "Innstillingane er lagra i .env.\n\n"
                f"API: {preview_key(values['OPENAI_API_KEY'])}\n"
                f"Inndata: {input_dir}\nNotat: {output_dir}\nKopi: {copy_dir}"
            ),
        )

    def _update_status(self, values: dict) -> None:
        if ENV_PATH.exists():
            msg = f".env funnen – siste kjende API: {preview_key(values.get('OPENAI_API_KEY', 'ukjent'))}"
        else:
            msg = "Ingen .env funnen enno."
        self.status_var.set(msg)


def main() -> None:
    root = tk.Tk()
    SetupApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
