import os
from pathlib import Path
import qrcode
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Any, Optional, cast
from qrcode.constants import ERROR_CORRECT_L
import pandas as pd

# Attempt to import openpyxl for .xlsx support
try:
    import openpyxl  # noqa: F401
    _has_openpyxl = True
except ImportError:
    _has_openpyxl = False


def create_qr_code(data: Any, filename: str, folder: Path, file_ext: str) -> Optional[Path]:
    """
    Generates and saves a QR code for the given data.
    Data can be any type; it will be converted to string internally.
    """
    data_str = str(data)
    if not data_str.strip():
        return None
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    folder.mkdir(parents=True, exist_ok=True)
    sanitized = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filepath = folder / f"{sanitized}.{file_ext}"
    img.save(cast(Any, filepath))  # type: ignore
    return filepath


def main() -> None:
    # Initialize root window
    root = tk.Tk()
    root.title("Batch QR Code Generator from Excel")
    root.geometry("650x300")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.configure("TLabel", font=(None, 10))
    style.configure("TButton", padding=6)
    style.configure("TEntry", padding=4)
    style.configure("TCombobox", padding=4)

    # Variables
    excel_path = tk.StringVar()
    save_folder = tk.StringVar(value=str(Path.home() / "Documents" / "QRCodes"))
    ext_var = tk.StringVar(value="png")

    # Layout configuration
    for i in range(4):
        root.rowconfigure(i, weight=1)
    root.columnconfigure(1, weight=1)

    # Excel file selection
    ttk.Label(root, text="Excel File:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
    excel_entry = ttk.Entry(root, textvariable=excel_path)
    excel_entry.grid(row=0, column=1, sticky="we", padx=8)
    ttk.Button(root, text="Browse", command=lambda: _select_excel(excel_path)).grid(row=0, column=2, sticky="w", padx=8)

    # Save folder selection
    ttk.Label(root, text="Save Folder:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
    folder_entry = ttk.Entry(root, textvariable=save_folder)
    folder_entry.grid(row=1, column=1, sticky="we", padx=8)
    ttk.Button(root, text="Browse", command=lambda: _select_folder(save_folder)).grid(row=1, column=2, sticky="w", padx=8)

    # File format
    ttk.Label(root, text="File Format:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
    ext_cb = ttk.Combobox(root, textvariable=ext_var, values=["png", "jpg"], state="readonly", width=8)
    ext_cb.grid(row=2, column=1, sticky="w", padx=8)

    # Generate button
    generate_btn = ttk.Button(root, text="Generate QR Codes", command=lambda: _process_excel(excel_path, save_folder, ext_var))
    generate_btn.grid(row=3, column=0, columnspan=3, pady=16)

    root.mainloop()


def _select_excel(var: tk.StringVar) -> None:
    path = filedialog.askopenfilename(
        title="Select Excel File",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if path:
        var.set(path)


def _select_folder(var: tk.StringVar) -> None:
    folder = filedialog.askdirectory(
        title="Select Save Folder",
        initialdir=var.get()
    )
    if folder:
        var.set(folder)


def _process_excel(excel_var: tk.StringVar, folder_var: tk.StringVar, ext_var: tk.StringVar) -> None:
    path = excel_var.get().strip()
    folder = Path(folder_var.get().strip())
    file_ext = ext_var.get().strip()

    if not path or not os.path.isfile(path):
        messagebox.showerror("Input Error", "Please select a valid Excel file.")
        return
    if path.lower().endswith("x") and not _has_openpyxl:
        messagebox.showerror("Dependency Error", "Please install 'openpyxl' to read .xlsx files.")
        return
    try:
        df = pd.read_excel(path, usecols=[0], header=None)
    except Exception as e:
        messagebox.showerror("Read Error", f"Failed to read Excel file:\n{e}")
        return

    values = df.iloc[:, 0].dropna().tolist()
    if not values:
        messagebox.showerror("Input Error", "No data found in the first column.")
        return

    count = 0
    for idx, data in enumerate(values, 1):
        name = str(data).strip() or f"qr_{idx}"
        if create_qr_code(data, name, folder, file_ext):
            count += 1

    messagebox.showinfo("Done", f"Generated {count}/{len(values)} QR codes.\nFolder: {folder}")

if __name__ == "__main__":
    main()