import os
from pathlib import Path
import qrcode
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
from qrcode.constants import ERROR_CORRECT_L


def create_qr_code(data: str, filename: str, folder: Path, file_ext: str) -> Optional[Path]:
    if not data.strip():
        messagebox.showerror("Input Error", "Please enter some text or a URL.")
        return None
    if not filename.strip():
        messagebox.showerror("Input Error", "Filename cannot be empty.")
        return None

    folder.mkdir(parents=True, exist_ok=True)
    filepath: Path = folder / f"{filename}.{file_ext}"

    qr: qrcode.QRCode = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)

    return filepath


def main() -> None:
    window: tk.Tk = tk.Tk()
    window.title("QR Code Generator")
    window.geometry("540x360")
    window.resizable(False, False)

    # Default folder path: User's Documents/QRCodes
    default_folder: Path = Path.home() / "Documents" / "QRCodes"

    # File extension options
    extensions = ["png", "jpg"]
    selected_ext = tk.StringVar(value="png")

    # --- Widgets ---
    tk.Label(window, text="Text or URL:").pack(pady=(10, 0))
    data_entry = tk.Entry(window, width=60)
    data_entry.pack(pady=5)

    tk.Label(window, text="Filename:").pack(pady=(10, 0))
    filename_entry = tk.Entry(window, width=60)
    filename_entry.pack(pady=5)

    tk.Label(window, text="File Format:").pack(pady=(10, 0))
    ext_dropdown = ttk.Combobox(window, textvariable=selected_ext, values=extensions, state="readonly", width=10)
    ext_dropdown.pack(pady=5)

    tk.Label(window, text="Save Folder Path:").pack(pady=(10, 0))
    folder_entry = tk.Entry(window, width=60)
    folder_entry.pack(pady=5)
    folder_entry.insert(0, str(default_folder))

    fullpath_preview_label = tk.Label(window, text="", fg="gray")
    fullpath_preview_label.pack(pady=(5, 0))

    # --- Functions ---
    def update_previews(*args: object) -> None:
        filename = filename_entry.get().strip()
        folder_path = folder_entry.get().strip()
        file_ext = selected_ext.get()
        sanitized_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

        # Update full path preview
        try:
            full_path = Path(folder_path) / f"{sanitized_filename}.{file_ext}"
            fullpath_preview_label.config(text=f"Full path: {full_path}")
        except Exception:
            fullpath_preview_label.config(text="Full path: (invalid path)")

    def update_filename_from_data(*args: object) -> None:
        data = data_entry.get().strip()
        suggested_name = data[:40].replace(" ", "_").replace("/", "_").replace("\\", "_") or "qr_code"
        filename_entry.delete(0, tk.END)
        filename_entry.insert(0, suggested_name)
        update_previews()

    def on_generate() -> None:
        data = data_entry.get().strip()
        filename = filename_entry.get().strip()
        folder_path = folder_entry.get().strip()
        file_ext = selected_ext.get()

        try:
            folder = Path(folder_path)
            filepath = create_qr_code(data, filename, folder, file_ext)
            if filepath:
                messagebox.showinfo("Success", f"QR code saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save QR code:\n{e}")

    # Bind events
    data_entry.bind("<KeyRelease>", update_filename_from_data)
    filename_entry.bind("<KeyRelease>", update_previews)
    folder_entry.bind("<KeyRelease>", update_previews)
    ext_dropdown.bind("<<ComboboxSelected>>", update_previews)

    tk.Button(window, text="Generate QR Code", command=on_generate).pack(pady=15)

    window.mainloop()


if __name__ == "__main__":
    main()
