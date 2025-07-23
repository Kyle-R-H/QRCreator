import os
import json
import uuid
import hashlib
from pathlib import Path
import qrcode
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from typing import Any, Optional, cast, Tuple
from qrcode.constants import ERROR_CORRECT_L
import pandas as pd

try:
    import openpyxl
    _has_openpyxl = True
except ImportError:
    _has_openpyxl = False

CONFIG_DIR = Path.home() / ".qr_generator_config"
CONFIG_FILE = CONFIG_DIR / "config.json"

def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_config(cfg: dict) -> None:
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(cfg))

def hash_password(pw: str, salt: str) -> str:
    return hashlib.sha256((salt + pw).encode()).hexdigest()

def set_password(pw: str) -> None:
    salt = uuid.uuid4().hex
    hashed = hash_password(pw, salt)
    cfg = {'salt': salt, 'pw_file': uuid.uuid4().hex + '.dat'}
    ensure_config_dir()
    salt_file = CONFIG_DIR / cfg['pw_file']
    salt_file.write_text(hashed)
    save_config(cfg)

def add_or_change_password_ui(root: tk.Tk) -> None:
    cfg = load_config()
    if cfg.get('pw_file'):
        old_pw = simpledialog.askstring("Current Password", "Enter current password:", show="*", parent=root)
        if not old_pw:
            return
        salt_file = CONFIG_DIR / cfg['pw_file']
        if not salt_file.exists() or hash_password(old_pw, cfg['salt']) != salt_file.read_text():
            messagebox.showerror("Error", "Incorrect current password.", parent=root)
            return

    new_pw = simpledialog.askstring("New Password", "Enter new password:", show="*", parent=root)
    if not new_pw:
        return
    confirm = simpledialog.askstring("Confirm Password", "Re-enter password:", show="*", parent=root)
    if new_pw != confirm:
        messagebox.showerror("Error", "Passwords do not match.", parent=root)
        return
    set_password(new_pw)
    messagebox.showinfo("Success", "Password set.", parent=root)

def remove_password_ui(root: tk.Tk) -> None:
    cfg = load_config()
    if not cfg.get('pw_file'):
        messagebox.showinfo("Info", "No password is set.", parent=root)
        return

    old_pw = simpledialog.askstring("Remove Password", "Enter current password:", show="*", parent=root)
    if not old_pw:
        return

    pw_file = CONFIG_DIR / cfg['pw_file']
    if not pw_file.exists() or hash_password(old_pw, cfg['salt']) != pw_file.read_text():
        messagebox.showerror("Error", "Incorrect password.", parent=root)
        return

    try:
        pw_file.unlink()
        CONFIG_FILE.unlink()
    except Exception:
        pass
    messagebox.showinfo("Removed", "Password removed.", parent=root)

def login_ui(root: tk.Tk) -> bool:
    cfg = load_config()
    if not cfg.get('pw_file'):
        return True
    pw_file = CONFIG_DIR / cfg['pw_file']
    if not pw_file.exists():
        return True
    stored_hash = pw_file.read_text()

    def forgot_password():
        messagebox.showinfo("Forgot Password?", "Contact the developer for help", parent=root)

    for _ in range(3):
        result = [False]
        pw_win = tk.Toplevel(root)
        pw_win.title("Login")
        pw_win.geometry("300x120")
        pw_win.grab_set()

        tk.Label(pw_win, text="Enter password:").pack(pady=(10, 0))
        pw_entry = tk.Entry(pw_win, show="*")
        pw_entry.pack(pady=5)

        def submit_pw():
            entered_pw = pw_entry.get()
            if hash_password(entered_pw, cfg['salt']) == stored_hash:
                result[0] = True
                pw_win.destroy()
            else:
                messagebox.showerror("Error", "Incorrect password.", parent=pw_win)

        tk.Button(pw_win, text="Submit", command=submit_pw).pack()
        tk.Button(pw_win, text="Forgot Password?", command=forgot_password).pack(pady=(5, 0))
        root.wait_window(pw_win)

        if result[0]:
            return True

    root.destroy()
    return False

# -----------------------------------------------------------
# Your Original QR Code Generator App with Password Features
# -----------------------------------------------------------
class QRCodeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QR Code Generator")
        self.root.geometry("650x400")
        self.root.resizable(False, False)

        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add/Change Password", command=lambda: add_or_change_password_ui(self.root))
        file_menu.add_command(label="Remove Password", command=lambda: remove_password_ui(self.root))
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.single_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.single_frame, text="Single QR Code")

        self.batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_frame, text="Batch from Excel")

        self._setup_single_tab()
        self._setup_batch_tab()

    def _setup_single_tab(self):
        style = ttk.Style(self.single_frame)
        style.configure("TLabel", font=(None, 10))
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=4)

        default_folder = Path.home() / "Documents" / "QRCodes"

        self.single_data = tk.StringVar()
        self.single_filename = tk.StringVar()
        self.single_folder = tk.StringVar(value=str(default_folder))
        self.single_ext = tk.StringVar(value="png")

        for i in range(5):
            self.single_frame.rowconfigure(i, weight=1)
        self.single_frame.columnconfigure(1, weight=1)

        ttk.Label(self.single_frame, text="Text:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        data_entry = ttk.Entry(self.single_frame, textvariable=self.single_data)
        data_entry.grid(row=0, column=1, sticky="we", padx=8)

        ttk.Label(self.single_frame, text="Filename:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        filename_entry = ttk.Entry(self.single_frame, textvariable=self.single_filename)
        filename_entry.grid(row=1, column=1, sticky="we", padx=8)

        ttk.Label(self.single_frame, text="File Format:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        ext_dropdown = ttk.Combobox(self.single_frame, textvariable=self.single_ext, values=["png", "jpg"], state="readonly", width=10)
        ext_dropdown.grid(row=2, column=1, sticky="w", padx=8)

        ttk.Label(self.single_frame, text="Save Folder:").grid(row=3, column=0, sticky="e", padx=8, pady=8)
        folder_entry = ttk.Entry(self.single_frame, textvariable=self.single_folder)
        folder_entry.grid(row=3, column=1, sticky="we", padx=8)
        ttk.Button(self.single_frame, text="Browse", command=self._select_single_folder).grid(row=3, column=2, sticky="w", padx=8)

        self.fullpath_preview_label = ttk.Label(self.single_frame, text="", foreground="gray")
        self.fullpath_preview_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 5))

        generate_btn = ttk.Button(self.single_frame, text="Generate QR Code", command=self._generate_single)
        generate_btn.grid(row=5, column=0, columnspan=3, pady=16)

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

        data_entry.bind("<KeyRelease>", update_filename_from_data)
        filename_entry.bind("<KeyRelease>", update_previews)
        folder_entry.bind("<KeyRelease>", update_previews)
        ext_dropdown.bind("<<ComboboxSelected>>", update_previews)

        update_filename_from_data()

    def _select_single_folder(self):
        folder = filedialog.askdirectory(title="Select Save Folder", initialdir=self.single_folder.get())
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

    def _setup_batch_tab(self):
        style = ttk.Style(self.batch_frame)
        style.configure("TLabel", font=(None, 10))
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=4)

        self.excel_path = tk.StringVar()
        self.save_folder = tk.StringVar(value=str(Path.home() / "Documents" / "QRCodes"))
        self.ext_var = tk.StringVar(value="png")

        for i in range(4):
            self.batch_frame.rowconfigure(i, weight=1)
        self.batch_frame.columnconfigure(1, weight=1)

        ttk.Label(self.batch_frame, text="Excel File:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        excel_entry = ttk.Entry(self.batch_frame, textvariable=self.excel_path)
        excel_entry.grid(row=0, column=1, sticky="we", padx=8)
        ttk.Button(self.batch_frame, text="Browse", command=self._select_excel).grid(row=0, column=2, sticky="w", padx=8)

        ttk.Label(self.batch_frame, text="Save Folder:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        folder_entry = ttk.Entry(self.batch_frame, textvariable=self.save_folder)
        folder_entry.grid(row=1, column=1, sticky="we", padx=8)
        ttk.Button(self.batch_frame, text="Browse", command=self._select_folder).grid(row=1, column=2, sticky="w", padx=8)

        ttk.Label(self.batch_frame, text="File Format:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        ext_cb = ttk.Combobox(self.batch_frame, textvariable=self.ext_var, values=["png", "jpg"], state="readonly", width=8)
        ext_cb.grid(row=2, column=1, sticky="w", padx=8)

        generate_btn = ttk.Button(self.batch_frame, text="Generate QR Codes", command=self._process_excel)
        generate_btn.grid(row=3, column=0, columnspan=3, pady=16)

    def _select_excel(self):
        path = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.excel_path.set(path)

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Save Folder", initialdir=self.save_folder.get())
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


def create_qr_code(data: Any, filename: str, folder: Path, file_ext: str) -> Optional[Path]:
    data_str = str(data).strip()
    if not data_str:
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
    safe_fn = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filepath = folder / f"{safe_fn}.{file_ext}"
    img.save(cast(Any, filepath))
    return filepath

if __name__ == "__main__":
    root = tk.Tk()
    if login_ui(root):
        app = QRCodeApp(root)
        root.mainloop()
