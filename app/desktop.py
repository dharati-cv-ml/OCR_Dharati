"""Windows-friendly desktop OCR inspector. Launch: python -m app.desktop

No HTTP server, no browser, no cloud calls. OCR is performed locally by Tesseract.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import threading
import tempfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk, ImageDraw, UnidentifiedImageError
import pytesseract

from app.main import MAX_BYTES, MAX_PIXELS, parse_fields

APP_NAME = "VisionInspect  •  OCR Studio"
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
BG = "#0b1220"
SURFACE = "#111d30"
SURFACE2 = "#17263b"
BORDER = "#2b3d56"
TEXT = "#edf3fb"
MUTED = "#9baec7"
ACCENT = "#5aabff"
GREEN = "#4bdea2"
RED = "#ff778b"
FONT = "Segoe UI"


def find_tesseract() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for location in (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Tesseract-OCR" / "tesseract.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    ):
        if location.is_file():
            return str(location)
    return None


def scan_file(path: str) -> dict:
    """Inspect a local file and return plain serializable data."""
    p = Path(path)
    if p.suffix.lower() not in SUPPORTED:
        raise ValueError("Unsupported format. Select PNG, JPG, WEBP, BMP or TIFF.")
    if p.stat().st_size > MAX_BYTES:
        raise ValueError("Image exceeds the 8 MB limit.")
    with Image.open(p) as source:
        source.verify()
    with Image.open(p) as source:
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("Image exceeds the 15-million-pixel limit.")
        source = ImageOps.exif_transpose(source).convert("RGB")
        gray = ImageOps.autocontrast(ImageOps.grayscale(source))
        # PSM 3 handles disconnected labels / barcode regions better than PSM 6
        # on the supplied packaging benchmark. Keep an independent second pass
        # only for fields missing from the first pass; never insert expected labels.
        extracted = pytesseract.image_to_string(gray, config="--psm 3").strip()
        first_fields = parse_fields(extracted)
        if any(value is None for value in first_fields):
            alternate = pytesseract.image_to_string(gray, config="--psm 6").strip()
            fallback_fields = parse_fields(alternate)
            if any(before is None and after is not None for before, after in zip(first_fields, fallback_fields)):
                extracted = extracted + "\n" + alternate
    product, batch, expiry = parse_fields(extracted)
    # Schema-aware correction for the documented synthetic PRD###### / B##### labels.
    from app.field_normalization import normalize_sample_fields
    raw_values = (product, batch, expiry)
    product, batch, expiry = normalize_sample_fields(product, batch, expiry)
    missing = [key for key, val in (("product_code", product), ("batch", batch), ("expiry", expiry)) if not val]
    return {
        "filename": p.name,
        "path": str(p),
        "raw_ocr_fields": dict(zip(("product_code", "batch", "expiry"), raw_values)),
        "product_code": product,
        "batch": batch,
        "expiry": expiry,
        "fields_found": 3 - len(missing),
        "passed": not missing,
        "warnings": ["Missing " + key.replace("_", " ") for key in missing],
        "extracted_text": extracted,
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
    }


class DesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1280x820")
        self.minsize(940, 640)
        self.configure(bg=BG)
        self.records: list[dict] = []
        self.selected_path: str | None = None
        self.preview_ref = None
        self.show_boxes = tk.BooleanVar(value=True)
        self._camera = None
        self._camera_job = None
        self._camera_frame = None
        self.busy = False
        self.tesseract_path = find_tesseract()
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        self._init_styles()
        self._build_ui()
        self.after(150, self._check_engine)

    def _init_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=SURFACE, foreground=TEXT, fieldbackground=SURFACE, rowheight=34,
                        borderwidth=0, font=(FONT, 10))
        style.configure("Treeview.Heading", background=SURFACE2, foreground=MUTED, font=(FONT, 10, "bold"),
                        relief="flat", padding=(9, 10))
        style.map("Treeview", background=[("selected", "#24558b")], foreground=[("selected", "#ffffff")])
        style.configure("App.Horizontal.TProgressbar", troughcolor=SURFACE2, background=ACCENT, borderwidth=0)

    def _label(self, parent, text, size=11, fg=TEXT, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=fg, font=(FONT, size, "bold" if bold else "normal"), **kw)

    def _button(self, parent, text, command, primary=False, width=None):
        return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else SURFACE2,
                         fg="#071324" if primary else TEXT, activebackground="#80c0ff" if primary else "#2b4261",
                         activeforeground="#081426" if primary else TEXT, relief="flat", cursor="hand2",
                         bd=0, font=(FONT, 10, "bold"), padx=18, pady=11, width=width)

    def _panel(self, parent):
        return tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)

    def _build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 18))
        tk.Label(header, text="◈", bg=BG, fg=ACCENT, font=(FONT, 26, "bold")).pack(side="left", padx=(0, 11))
        title = tk.Frame(header, bg=BG)
        title.pack(side="left")
        self._label(title, "VisionInspect", 22, bold=True).pack(anchor="w")
        self._label(title, "Industrial OCR inspection  /  Private, local processing", 10, MUTED).pack(anchor="w")
        self.engine_label = tk.Label(header, bg=BG, fg=MUTED, font=(FONT, 10))
        self.engine_label.pack(side="right", padx=(15, 0))

        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=28, pady=(0, 18))
        self.pick_btn = self._button(toolbar, "+  Select image", self.pick_image, primary=True)
        self.pick_btn.pack(side="left", padx=(0, 9))
        self.folder_btn = self._button(toolbar, "▣  Scan folder", self.pick_folder)
        self.folder_btn.pack(side="left", padx=(0, 9))
        self.scan_btn = self._button(toolbar, "▶  Inspect image", self.inspect_selected)
        self.scan_btn.pack(side="left", padx=(0, 9))
        self.camera_btn = self._button(toolbar, "◎  Camera", self.open_camera)
        self.camera_btn.pack(side="left", padx=(0, 9))
        self.analytics_btn = self._button(toolbar, "▥  Analytics", self.show_analytics)
        self.analytics_btn.pack(side="left", padx=(0, 9))
        self._button(toolbar, "↓  Export CSV", self.export_csv).pack(side="right")
        self._button(toolbar, "↓  Export JSON", self.export_json).pack(side="right", padx=(0, 8))

        stats = tk.Frame(self, bg=BG)
        stats.pack(fill="x", padx=28, pady=(0, 17))
        self.total_var = tk.StringVar(value="0")
        self.pass_var = tk.StringVar(value="0")
        self.fail_var = tk.StringVar(value="0")
        self.fields_var = tk.StringVar(value="0")
        for i, (heading, var, color) in enumerate((("IMAGES SCANNED", self.total_var, TEXT),
                                                    ("PASSED", self.pass_var, GREEN),
                                                    ("NEEDS REVIEW", self.fail_var, RED),
                                                    ("FIELDS EXTRACTED", self.fields_var, ACCENT))):
            card = self._panel(stats)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 5, 5 if i < 3 else 0), ipadx=15, ipady=10)
            stats.grid_columnconfigure(i, weight=1)
            self._label(card, heading, 9, MUTED, bold=True).pack(anchor="w", padx=14, pady=(5, 5))
            self._label(card, "", 22, color, bold=True, textvariable=var).pack(anchor="w", padx=14, pady=(0, 4))

        body = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=9, bd=0)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 14))
        left = self._panel(body)
        right = self._panel(body)
        body.add(left, minsize=340, stretch="always")
        body.add(right, minsize=400, stretch="always")
        self._label(left, "IMAGE PREVIEW", 10, MUTED, bold=True).pack(anchor="w", padx=20, pady=(18, 10))
        self.preview_canvas = tk.Label(left, bg="#101a2a", text="Select an image to preview", fg=MUTED, compound="center")
        self.preview_canvas.pack(fill="both", expand=True, padx=17, pady=(0, 8))
        self.preview_canvas.bind("<Configure>", lambda e: self.after_idle(self._redraw_preview))
        self.file_label = self._label(left, "Choose an image to begin", 10, MUTED, anchor="w")
        self.file_label.pack(fill="x", padx=20, pady=(0, 8))
        tk.Checkbutton(left, text="Show OCR bounding boxes", variable=self.show_boxes, command=self._redraw_preview,
                       bg=SURFACE, fg=MUTED, selectcolor=SURFACE2, activebackground=SURFACE,
                       activeforeground=TEXT).pack(anchor="w", padx=20, pady=(0, 12))

        self._label(right, "INSPECTION RESULTS", 10, MUTED, bold=True).pack(anchor="w", padx=20, pady=(18, 10))
        self.result_badge = self._label(right, "WAITING FOR IMAGE", 13, MUTED, bold=True)
        self.result_badge.pack(anchor="w", padx=20, pady=(0, 14))
        grid = tk.Frame(right, bg=SURFACE)
        grid.pack(fill="x", padx=20)
        self.detail_labels: dict[str, tk.Label] = {}
        for index, (key, friendly) in enumerate((("product_code", "PRODUCT CODE"), ("batch", "LOT / BATCH"), ("expiry", "EXPIRY"))):
            field = tk.Frame(grid, bg=SURFACE2, padx=14, pady=11)
            field.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            grid.grid_columnconfigure(0, weight=1)
            self._label(field, friendly, 9, MUTED, bold=True).pack(anchor="w")
            val = self._label(field, "—", 13, TEXT, bold=True)
            val.pack(anchor="w", pady=(4, 0))
            self.detail_labels[key] = val
        self.metrics_label = self._label(right, "OCR confidence: —  |  Processing: —  |  Codes: —", 10, ACCENT)
        self.metrics_label.pack(anchor="w", padx=20, pady=(2, 6))
        self.codes_label = self._label(right, "QR / Data Matrix: —", 10, MUTED)
        self.codes_label.pack(anchor="w", padx=20, pady=(0, 6))
        self._label(right, "EXTRACTED TEXT", 9, MUTED, bold=True).pack(anchor="w", padx=20, pady=(12, 7))
        text_holder = tk.Frame(right, bg=SURFACE)
        text_holder.pack(fill="both", expand=True, padx=20, pady=(0, 13))
        self.textbox = tk.Text(text_holder, bg="#0d1726", fg=TEXT, insertbackground=TEXT, wrap="word", relief="flat",
                               padx=13, pady=13, font=("Consolas", 10), height=7)
        scroll = ttk.Scrollbar(text_holder, orient="vertical", command=self.textbox.yview)
        self.textbox.configure(yscrollcommand=scroll.set)
        self.textbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._button(right, "Copy extracted text", self.copy_text).pack(anchor="e", padx=20, pady=(0, 15))

        bottom = self._panel(self)
        bottom.pack(fill="both", expand=False, padx=28, pady=(0, 14))
        bar = tk.Frame(bottom, bg=SURFACE)
        bar.pack(fill="x", padx=15, pady=(12, 7))
        self._label(bar, "INSPECTION HISTORY", 10, MUTED, bold=True).pack(side="left")
        self._button(bar, "Clear history", self.clear_history).pack(side="right")
        table_holder = tk.Frame(bottom, bg=SURFACE)
        table_holder.pack(fill="both", expand=True, padx=14, pady=(0, 13))
        cols = ("name", "result", "product", "batch", "expiry", "fields")
        self.table = ttk.Treeview(table_holder, columns=cols, show="headings", height=5, selectmode="browse")
        for col, heading, width in (("name", "Image", 190), ("result", "Status", 120), ("product", "Product code", 155),
                                    ("batch", "Batch", 130), ("expiry", "Expiry", 130), ("fields", "Fields", 70)):
            self.table.heading(col, text=heading)
            self.table.column(col, width=width, anchor="w" if col != "fields" else "center")
        self.table.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_holder, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.bind("<<TreeviewSelect>>", self.show_history_selection)

        statusbar = tk.Frame(self, bg=BG)
        statusbar.pack(fill="x", padx=28, pady=(0, 15))
        self.status_var = tk.StringVar(value="Ready · All images processed on this computer")
        self._label(statusbar, "", 10, MUTED, textvariable=self.status_var).pack(side="left")
        self.progress = ttk.Progressbar(statusbar, mode="determinate", length=160, style="App.Horizontal.TProgressbar")
        self.progress.pack(side="right")
        self._redraw_preview()

    def _check_engine(self):
        if self.tesseract_path:
            self.engine_label.config(text="●  OCR ENGINE READY", fg=GREEN)
        else:
            self.engine_label.config(text="●  TESSERACT NOT FOUND", fg=RED)
            self.status_var.set("Tesseract OCR is missing; install it to scan images")
            messagebox.showwarning("OCR engine not found", "Tesseract OCR is required to read text.\n\nInstall Tesseract for Windows and restart the app.\nSee README_DESKTOP.md for instructions.")

    def pick_image(self):
        choice = filedialog.askopenfilename(title="Select product packaging image",
                                            filetypes=[("Supported images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")])
        if choice:
            self.selected_path = choice
            self.file_label.config(text=Path(choice).name)
            self._redraw_preview()
            self.status_var.set("Image selected · Click Inspect image")

    def pick_folder(self):
        folder = filedialog.askdirectory(title="Choose folder with packaging images")
        if not folder:
            return
        files = [str(x) for x in sorted(Path(folder).iterdir()) if x.is_file() and x.suffix.lower() in SUPPORTED]
        if not files:
            messagebox.showinfo("No images", "This folder has no supported images.")
            return
        self._run_scans(files)

    def inspect_selected(self):
        if not self.selected_path:
            messagebox.showinfo("Choose image", "Click Select image first.")
            return
        self._run_scans([self.selected_path])

    def _run_scans(self, files):
        if self.busy:
            return
        if not self.tesseract_path:
            messagebox.showerror("OCR unavailable", "Tesseract OCR is not installed or not found. See README_DESKTOP.md.")
            return
        self.busy = True
        self.progress.configure(value=0, maximum=len(files))
        self.status_var.set(f"Scanning 0 of {len(files)} images...")
        for b in (self.pick_btn, self.folder_btn, self.scan_btn, self.camera_btn):
            b.config(state="disabled")

        def worker():
            for index, path in enumerate(files, start=1):
                try:
                    from app.advanced import inspect_advanced
                    result = inspect_advanced(path)
                except Exception as exc:
                    result = {"filename": Path(path).name, "path": path, "product_code": None, "batch": None,
                              "expiry": None, "fields_found": 0, "passed": False,
                              "warnings": [f"Processing error: {exc}"], "extracted_text": "",
                              "scanned_at": datetime.now().isoformat(timespec="seconds")}
                self.after(0, lambda record=result, n=index: self._accept_scan(record, n, len(files)))
            self.after(0, self._finish_scan)
        threading.Thread(target=worker, daemon=True).start()

    def _accept_scan(self, record, n, count):
        # Persistent local audit trail (never uploads customer images or data).
        try:
            from app.track_trace import save_inspection
            audit_dir = Path.home() / 'VisionInspect'
            audit_dir.mkdir(parents=True, exist_ok=True)
            record['audit_id'] = save_inspection(audit_dir / 'inspection_history.sqlite3', record)
        except Exception as exc:
            record.setdefault('warnings', []).append(f'Audit storage unavailable: {exc}')
        self.records.append(record)
        idx = len(self.records)-1
        self.table.insert("", "end", iid=str(idx), values=(record["filename"], "PASS" if record["passed"] else "REVIEW",
                                                        record["product_code"] or "—", record["batch"] or "—",
                                                        record["expiry"] or "—", f'{record["fields_found"]}/3'))
        self.total_var.set(str(len(self.records)))
        self.pass_var.set(str(sum(r["passed"] for r in self.records)))
        self.fail_var.set(str(sum(not r["passed"] for r in self.records)))
        self.fields_var.set(str(sum(r["fields_found"] for r in self.records)))
        self.progress.configure(value=n)
        self.status_var.set(f"Scanned {n} of {count} images")
        self.table.selection_set(str(idx))
        self.table.see(str(idx))
        self._show_record(record)

    def _finish_scan(self):
        self.busy = False
        for b in (self.pick_btn, self.folder_btn, self.scan_btn, self.camera_btn):
            b.config(state="normal")
        self.status_var.set("Inspection complete · Export your results to CSV or JSON")

    def _show_record(self, record):
        self.result_badge.config(text="✓  PASS — ALL FIELDS FOUND" if record["passed"] else "!  NEEDS REVIEW", fg=GREEN if record["passed"] else RED)
        for key, label in self.detail_labels.items():
            label.config(text=record.get(key) or "Not detected", fg=TEXT if record.get(key) else RED)
        extracted = record["extracted_text"]
        notes = "\n\n⚠ " + " | ".join(record["warnings"]) if record["warnings"] else ""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", (extracted or "No readable text detected") + notes)
        self.textbox.configure(state="disabled")
        confidence = record.get("average_confidence")
        self.metrics_label.config(text=f"OCR confidence: {confidence if confidence is not None else '—'}  |  Processing: {record.get('processing_ms', '—')} ms  |  Codes: {len(record.get('barcodes', []))}")
        codes = record.get("barcodes", [])
        code_label = "; ".join(f"{x['format']}: {x['text'][:90]}" for x in codes[:3]) or record.get('barcode_error') or "No code detected"
        self.codes_label.config(text=f"Barcode comparison: {record.get('barcode_status', '—')} | QR / Data Matrix: {code_label[:95]}")
        self.selected_path = record["path"]
        self.file_label.config(text=record["filename"])
        self._redraw_preview()

    def show_history_selection(self, _event=None):
        selected = self.table.selection()
        if selected:
            idx = int(selected[0])
            if idx < len(self.records):
                self._show_record(self.records[idx])

    def _redraw_preview(self):
        """Display the image on a persistent Label; draw scaled rectangles in Pillow.

        Using a Canvas image could leave an empty preview after layout changes on
        some Windows/Tk versions. A Label keeps a strong image reference.
        """
        widget = self.preview_canvas
        if not self.selected_path:
            widget.configure(image="", text="Select an image to preview")
            self.preview_ref = None
            return
        try:
            with Image.open(self.selected_path) as src:
                image = ImageOps.exif_transpose(src).convert("RGB")
            source_w, source_h = image.size
            available_w = max(280, widget.winfo_width() - 24)
            available_h = max(240, widget.winfo_height() - 24)
            # Keep the preview at a manageable size even before Tk lays out widgets.
            image.thumbnail((min(available_w, 1000), min(available_h, 850)), Image.Resampling.LANCZOS)
            record = next((r for r in reversed(self.records) if r.get("path") == self.selected_path), None)
            if self.show_boxes.get() and record:
                draw = ImageDraw.Draw(image)
                sx, sy = image.width / source_w, image.height / source_h
                for b in record.get("boxes", []):
                    xy = (int(b["x"]*sx), int(b["y"]*sy), int((b["x"]+b["w"])*sx), int((b["y"]+b["h"])*sy))
                    draw.rectangle(xy, outline="#26ee92", width=2)
                for code in record.get("barcodes", []):
                    points = code.get("position", [])
                    if len(points) >= 4:
                        coords = [(int(pt[0]*sx), int(pt[1]*sy)) for pt in points]
                        draw.line(coords + [coords[0]], fill="#ffbc4b", width=4)
            self.preview_ref = ImageTk.PhotoImage(image, master=self)
            widget.configure(image=self.preview_ref, text="")
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            widget.configure(image="", text=f"Preview unavailable: {exc}")
            self.preview_ref = None

    def copy_text(self):
        text = self.textbox.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status_var.set("Extracted text copied to clipboard")

    def export_csv(self):
        if not self.records:
            messagebox.showinfo("Nothing to export", "Scan an image first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="ocr_inspection_results.csv")
        if not path:
            return
        keys = ("filename", "product_code", "batch", "expiry", "fields_found", "passed", "warnings", "extracted_text", "scanned_at", "average_confidence", "processing_ms", "barcodes", "barcode_status", "barcode_verified", "field_comparison")
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for result in self.records:
                    writer.writerow({key: " | ".join(result[key]) if key == "warnings" else json.dumps(result.get(key), ensure_ascii=False) if key in ("barcodes", "field_comparison") else result.get(key) for key in keys})
            self.status_var.set(f"CSV saved · {Path(path).name}")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))

    def export_json(self):
        if not self.records:
            messagebox.showinfo("Nothing to export", "Scan an image first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="ocr_inspection_results.json")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
            self.status_var.set(f"JSON saved · {Path(path).name}")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))

    def clear_history(self):
        if self.busy:
            return
        self.records.clear()
        for item in self.table.get_children():
            self.table.delete(item)
        for var in (self.total_var, self.pass_var, self.fail_var, self.fields_var):
            var.set("0")
        self.result_badge.config(text="WAITING FOR IMAGE", fg=MUTED)
        for label in self.detail_labels.values():
            label.config(text="—", fg=TEXT)
        self.textbox.config(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.config(state="disabled")
        self.progress.configure(value=0)
        self.metrics_label.config(text="OCR confidence: —  |  Processing: —  |  Codes: —")
        self.codes_label.config(text="QR / Data Matrix: —")
        self.status_var.set("Inspection history cleared")



    def show_analytics(self):
        from app.advanced import summarize
        stats = summarize(self.records)
        window = tk.Toplevel(self)
        window.title("VisionInspect • Inspection Analytics")
        window.geometry("540x410")
        window.configure(bg=BG)
        self._label(window, "INSPECTION ANALYTICS", 19, bold=True).pack(anchor="w", padx=26, pady=(22,18))
        lines = [("Total inspections", stats['total']), ("Passed", stats['passed']),
                 ("Needs review", stats['needs_review']), ("Pass rate", f"{stats['pass_rate']}%"),
                 ("Average processing", f"{stats['mean_processing_ms']} ms" if stats['mean_processing_ms'] is not None else "—"),
                 ("Decoded QR / Data Matrix", stats['codes_found'])]
        for name, val in lines:
            line = tk.Frame(window, bg=SURFACE, padx=14, pady=9)
            line.pack(fill="x", padx=24, pady=3)
            self._label(line, name, 11, MUTED).pack(side="left")
            self._label(line, str(val), 12, GREEN if name == "Passed" else TEXT, bold=True).pack(side="right")

    def open_camera(self):
        if self.busy:
            return
        try:
            import cv2
        except ImportError:
            messagebox.showerror("Camera dependency", "Install OpenCV with pip: python -m pip install opencv-python")
            return
        if self._camera is not None:
            return
        capture = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == 'nt' else cv2.VideoCapture(0)
        if not capture.isOpened():
            capture.release()
            messagebox.showerror("Camera unavailable", "Cannot open camera 0. Check permissions and whether another application is using it.")
            return
        self._camera = capture
        window = tk.Toplevel(self)
        window.title("Camera Capture • VisionInspect")
        window.geometry("820x650")
        window.configure(bg=BG)
        label = tk.Label(window, bg=BG)
        label.pack(fill="both", expand=True, padx=18, pady=15)
        def close():
            if self._camera_job:
                try: window.after_cancel(self._camera_job)
                except tk.TclError: pass
                self._camera_job = None
            if self._camera is not None:
                self._camera.release()
                self._camera = None
            window.destroy()
        def snapshot():
            if self._camera_frame is None:
                return
            rgb = cv2.cvtColor(self._camera_frame, cv2.COLOR_BGR2RGB)
            target = Path(tempfile.gettempdir()) / f"visioninspect_capture_{datetime.now():%Y%m%d_%H%M%S_%f}.png"
            Image.fromarray(rgb).save(target)
            self.selected_path = str(target)
            self.file_label.config(text=target.name)
            close()
            self._redraw_preview()
            self.inspect_selected()
        self._button(window, "Capture & inspect", snapshot, primary=True).pack(pady=(0,15))
        def update():
            if self._camera is None or not window.winfo_exists():
                return
            ok, frame = self._camera.read()
            if ok:
                self._camera_frame = frame.copy()
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(rgb)
                im.thumbnail((780,530))
                photo = ImageTk.PhotoImage(im)
                label.config(image=photo)
                label.image = photo
            self._camera_job = window.after(55, update)
        window.protocol("WM_DELETE_WINDOW", close)
        update()


def main():
    DesktopApp().mainloop()


if __name__ == "__main__":
    main()
