import os
from pathlib import Path
import qrcode
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Optional, Any, cast
from qrcode.constants import ERROR_CORRECT_L
import pandas as pd

# Attempt to import openpyxl for .xlsx support
try:
    import openpyxl 
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
        messagebox.showerror("Input Error", "Please enter some text.")
        return None
    if not filename.strip():
        messagebox.showerror("Input Error", "Filename cannot be empty.")
        return None

    folder.mkdir(parents=True, exist_ok=True)
    sanitized = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filepath = folder / f"{sanitized}.{file_ext}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(cast(Any, filepath)) 
    return filepath


class QRCodeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QR Code Generator")
        self.root.geometry("650x400")
        self.root.resizable(False, False)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        # Single tab frame
        self.single_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.single_frame, text="Single QR Code")

        # Batch tab frame
        self.batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_frame, text="Batch from Excel")

        self._setup_single_tab()
        self._setup_batch_tab()

    # ------------------
    # Single QR code tab
    # ------------------
    def _setup_single_tab(self):
        style = ttk.Style(self.single_frame)
        style.configure("TLabel", font=(None, 10))
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=4)

        # Default folder path
        default_folder = Path.home() / "Documents" / "QRCodes"

        # Variables
        self.single_data = tk.StringVar()
        self.single_filename = tk.StringVar()
        self.single_folder = tk.StringVar(value=str(default_folder))
        self.single_ext = tk.StringVar(value="png")

        # Layout config
        for i in range(5):
            self.single_frame.rowconfigure(i, weight=1)
        self.single_frame.columnconfigure(1, weight=1)

        # Text input
        ttk.Label(self.single_frame, text="Text:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        data_entry = ttk.Entry(self.single_frame, textvariable=self.single_data)
        data_entry.grid(row=0, column=1, sticky="we", padx=8)

        # Filename
        ttk.Label(self.single_frame, text="Filename:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        filename_entry = ttk.Entry(self.single_frame, textvariable=self.single_filename)
        filename_entry.grid(row=1, column=1, sticky="we", padx=8)

        # File format
        ttk.Label(self.single_frame, text="File Format:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        ext_dropdown = ttk.Combobox(self.single_frame, textvariable=self.single_ext, values=["png", "jpg"], state="readonly", width=10)
        ext_dropdown.grid(row=2, column=1, sticky="w", padx=8)

        # Save folder
        ttk.Label(self.single_frame, text="Save Folder:").grid(row=3, column=0, sticky="e", padx=8, pady=8)
        folder_entry = ttk.Entry(self.single_frame, textvariable=self.single_folder)
        folder_entry.grid(row=3, column=1, sticky="we", padx=8)
        ttk.Button(self.single_frame, text="Browse", command=self._select_single_folder).grid(row=3, column=2, sticky="w", padx=8)

        # Preview label
        self.fullpath_preview_label = ttk.Label(self.single_frame, text="", foreground="gray")
        self.fullpath_preview_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 5))

        # Generate button
        generate_btn = ttk.Button(self.single_frame, text="Generate QR Code", command=self._generate_single)
        generate_btn.grid(row=5, column=0, columnspan=3, pady=16)

        # --- Functions ---
        def update_previews(*args: object) -> None:
            filename = self.single_filename.get().strip()
            folder_path = self.single_folder.get().strip()
            file_ext = self.single_ext.get()
            sanitized = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
            try:
                full_path = Path(folder_path) / f"{sanitized}.{file_ext}"
                self.fullpath_preview_label.config(text=f"Full path: {full_path}")
            except Exception:
                self.fullpath_preview_label.config(text="Full path: (invalid path)")

        def update_filename_from_data(*args: object) -> None:
            data = self.single_data.get().strip()
            suggested = data[:40].replace(" ", "_").replace("/", "_").replace("\\", "_") or "qr_code"
            self.single_filename.set(suggested)
            update_previews()

        # Bindings
        data_entry.bind("<KeyRelease>", update_filename_from_data)
        filename_entry.bind("<KeyRelease>", update_previews)
        folder_entry.bind("<KeyRelease>", update_previews)
        ext_dropdown.bind("<<ComboboxSelected>>", update_previews)

        update_filename_from_data()

    def _select_single_folder(self):
        folder = filedialog.askdirectory(
            title="Select Save Folder",
            initialdir=self.single_folder.get()
        )
        if folder:
            self.single_folder.set(folder)

    def _generate_single(self):
        data = self.single_data.get().strip()
        filename = self.single_filename.get().strip()
        folder_path = self.single_folder.get().strip()
        file_ext = self.single_ext.get()

        try:
            folder = Path(folder_path)
            filepath = create_qr_code(data, filename, folder, file_ext)
            if filepath:
                messagebox.showinfo("Success", f"QR code saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save QR code:\n{e}")




    # -----------------
    # Batch QR code tab
    # -----------------
    def _setup_batch_tab(self):
        style = ttk.Style(self.batch_frame)
        style.configure("TLabel", font=(None, 10))
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=4)

        # Variables
        self.excel_path = tk.StringVar()
        self.save_folder = tk.StringVar(value=str(Path.home() / "Documents" / "QRCodes"))
        self.ext_var = tk.StringVar(value="png")

        # Layout configuration
        for i in range(4):
            self.batch_frame.rowconfigure(i, weight=1)
        self.batch_frame.columnconfigure(1, weight=1)

        # Excel file selection
        ttk.Label(self.batch_frame, text="Excel File:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        excel_entry = ttk.Entry(self.batch_frame, textvariable=self.excel_path)
        excel_entry.grid(row=0, column=1, sticky="we", padx=8)
        ttk.Button(self.batch_frame, text="Browse", command=self._select_excel).grid(row=0, column=2, sticky="w", padx=8)

        # Save folder selection
        ttk.Label(self.batch_frame, text="Save Folder:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        folder_entry = ttk.Entry(self.batch_frame, textvariable=self.save_folder)
        folder_entry.grid(row=1, column=1, sticky="we", padx=8)
        ttk.Button(self.batch_frame, text="Browse", command=self._select_folder).grid(row=1, column=2, sticky="w", padx=8)

        # File format
        ttk.Label(self.batch_frame, text="File Format:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        ext_cb = ttk.Combobox(self.batch_frame, textvariable=self.ext_var, values=["png", "jpg"], state="readonly", width=8)
        ext_cb.grid(row=2, column=1, sticky="w", padx=8)

        # Generate button
        generate_btn = ttk.Button(self.batch_frame, text="Generate QR Codes", command=self._process_excel)
        generate_btn.grid(row=3, column=0, columnspan=3, pady=16)

    def _select_excel(self):
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if path:
            self.excel_path.set(path)

    def _select_folder(self):
        folder = filedialog.askdirectory(
            title="Select Save Folder",
            initialdir=self.save_folder.get()
        )
        if folder:
            self.save_folder.set(folder)

    def _process_excel(self):
        path = self.excel_path.get().strip()
        folder = Path(self.save_folder.get().strip())
        file_ext = self.ext_var.get().strip()

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

        messagebox.showinfo("Done", f"Generated {count} QR code(s) in:\n{folder}")


if __name__ == "__main__":
    root = tk.Tk()
    app = QRCodeApp(root)
    root.mainloop()
