import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import qrcode
import cv2
import os
import io
import win32clipboard
import win32con
import tempfile
import numpy as np

# --- Core Logic ---
def generate_qr(data, size=8):
    if not data.strip():
        return None
    qr = qrcode.QRCode(version=1, box_size=size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def read_qr(image_path):
    try:
        img = cv2.imread(image_path)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        return data if data else None
    except Exception:
        return None

# --- Graphical User Interface ---
class QRToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Tool")
        self.root.geometry("360x520")
        self.root.resizable(False, False)

        self.qr_image = None
        self.qr_photo = None
        self.qr_bmp_data = None

        # --- UI Styling ---
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Result.TLabel", font=("Consolas", 11), foreground="#005A9E")
        style.configure("Status.TLabel", font=("Segoe UI", 8), foreground="#888888")

        # --- Tabs ---

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.gen_frame = ttk.Frame(self.notebook)
        self.read_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gen_frame, text="  Generate  ")
        self.notebook.add(self.read_frame, text="  Read  ")

        self.build_generate_tab()
        self.build_read_tab()

        # Status Bar
        self.status_label = ttk.Label(root, text="Paste text or URL to generate a QR code", style="Status.TLabel")
        self.status_label.pack(side="bottom", pady=10)

    # --- Generate Tab ---
    def build_generate_tab(self):
        ttk.Label(self.gen_frame, text="Enter text or URL:", style="Title.TLabel").pack(pady=(20, 5))

        self.input_entry = ttk.Entry(self.gen_frame, width=35, justify="center", font=("Segoe UI", 10))
        self.input_entry.pack(pady=5)
        self.input_entry.focus_set()
        self.input_entry.bind("<KeyRelease>", lambda e: self.on_input_change())

        # QR Preview (clickable — copies image)
        self.qr_canvas = tk.Canvas(self.gen_frame, width=200, height=200, bg="white", highlightthickness=1, highlightbackground="#CCCCCC", cursor="hand2")
        self.qr_canvas.pack(pady=(15, 10))
        self.qr_canvas.bind("<Button-1>", lambda e: self.copy_qr_image())

        # Buttons
        btn_frame = ttk.Frame(self.gen_frame)
        btn_frame.pack(pady=5)

        self.save_btn = ttk.Button(btn_frame, text="Save as PNG", command=self.save_qr)
        self.save_btn.pack(side="left", padx=5)

        self.copy_btn = ttk.Button(btn_frame, text="Copy to Clipboard", command=self.copy_qr)
        self.copy_btn.pack(side="left", padx=5)

    def on_input_change(self):
        data = self.input_entry.get()
        if not data.strip():
            self.qr_canvas.delete("all")
            self.qr_image = None
            self.qr_bmp_data = None
            self.status_label.config(text="Paste text or URL to generate a QR code")
            return

        img = generate_qr(data, size=8)
        if img:
            self.qr_image = img
            # Prerender BMP for clipboard at the same time as display
            bmp_buffer = io.BytesIO()
            img.save(bmp_buffer, format="BMP")
            self.qr_bmp_data = bmp_buffer.getvalue()
            # Display
            display = img.resize((200, 200), Image.NEAREST)
            self.qr_photo = ImageTk.PhotoImage(display)
            self.qr_canvas.delete("all")
            self.qr_canvas.create_image(100, 100, image=self.qr_photo)
            self.status_label.config(text=f"QR generated — click QR to copy image")

    def save_qr(self):
        if not self.qr_image:
            self.status_label.config(text="Nothing to save — enter some text first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if path:
            self.qr_image.save(path)
            self.status_label.config(text=f"Saved to {os.path.basename(path)}")

    def copy_qr_image(self):
        if not self.qr_image:
            self.status_label.config(text="Nothing to copy — enter some text first")
            return
        self._copy_image_to_clipboard(self.qr_image)
        self.status_label.config(text="QR image copied to clipboard!")
        # Brief visual feedback
        self.qr_canvas.config(highlightbackground="#005A9E")
        self.root.after(1000, lambda: self.qr_canvas.config(highlightbackground="#CCCCCC"))

    def copy_qr(self):
        if not self.qr_image:
            self.status_label.config(text="Nothing to copy — enter some text first")
            return
        self._copy_image_to_clipboard(self.qr_image)
        self.copy_btn.config(text="Copied!")
        self.status_label.config(text="QR image copied to clipboard!")
        self.root.after(2000, lambda: self.copy_btn.config(text="Copy to Clipboard"))

    def _copy_image_to_clipboard(self, pil_image):
        # Convert to BMP and copy as DIB (best format for Windows clipboard)
        output = io.BytesIO()
        pil_image.convert("RGB").save(output, format="BMP")
        bmp_data = output.getvalue()
        # Strip the 14-byte BMP file header to get raw DIB data
        dib_data = bmp_data[14:]
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_data)
        win32clipboard.CloseClipboard()

    # --- Read Tab ---
    def build_read_tab(self):
        ttk.Label(self.read_frame, text="Read a QR Code:", style="Title.TLabel").pack(pady=(20, 5))

        # Drop zone (clickable to open file)
        self.drop_canvas = tk.Canvas(self.read_frame, width=200, height=200, bg="white", highlightthickness=1, highlightbackground="#CCCCCC", cursor="hand2")
        self.drop_canvas.pack(pady=(10, 5))
        self.drop_canvas.create_text(100, 85, text="Click here to", font=("Segoe UI", 10), fill="#AAAAAA")
        self.drop_canvas.create_text(100, 105, text="open an image", font=("Segoe UI", 10), fill="#AAAAAA")
        self.drop_canvas.create_text(100, 130, text="PNG, JPG, BMP, WEBP  |  Ctrl+V to paste", font=("Segoe UI", 8), fill="#CCCCCC")
        self.drop_canvas.bind("<Button-1>", lambda e: self.open_image())

        # Ctrl+V paste from clipboard
        self.root.bind("<Control-v>", lambda e: self.paste_from_clipboard())

        self.open_btn = ttk.Button(self.read_frame, text="Open Image", command=self.open_image)
        self.open_btn.pack(pady=10)

        # Result
        ttk.Label(self.read_frame, text="Decoded content:", font=("Segoe UI", 10)).pack(pady=(10, 2))

        self.result_text = tk.Text(self.read_frame, height=3, width=35, font=("Consolas", 10), wrap="word", state="disabled", bg="#F5F5F5", relief="flat", borderwidth=1)
        self.result_text.pack(padx=15)

        self.copy_result_btn = ttk.Button(self.read_frame, text="Copy Result", command=self.copy_result)
        self.copy_result_btn.pack(pady=8)

    def paste_from_clipboard(self):
        # Switch to Read tab
        self.notebook.select(self.read_frame)
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                dib_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                win32clipboard.CloseClipboard()
                # DIB to PIL Image
                # Add BMP file header (14 bytes) to make it a valid BMP
                bmp_header = b'BM' + (len(dib_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                bmp_data = bmp_header + dib_data
                img = Image.open(io.BytesIO(bmp_data))
                self._process_pasted_image(img)
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                # File paths on clipboard
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                win32clipboard.CloseClipboard()
                if files:
                    self._load_image_file(files[0])
            else:
                win32clipboard.CloseClipboard()
                self.status_label.config(text="No image found in clipboard")
        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
            self.status_label.config(text="Could not read clipboard")

    def _process_pasted_image(self, img):
        # Show preview
        img_display = img.resize((200, 200), Image.LANCZOS)
        self.drop_photo = ImageTk.PhotoImage(img_display)
        self.drop_canvas.delete("all")
        self.drop_canvas.create_image(100, 100, image=self.drop_photo)

        # Save to temp for cv2 decoding
        tmp = os.path.join(tempfile.gettempdir(), "qr_paste_tmp.png")
        img.save(tmp, format="PNG")
        result = read_qr(tmp)
        self._show_read_result(result)

    def _load_image_file(self, path):
        try:
            img = Image.open(path)
            img_display = img.resize((200, 200), Image.LANCZOS)
            self.drop_photo = ImageTk.PhotoImage(img_display)
            self.drop_canvas.delete("all")
            self.drop_canvas.create_image(100, 100, image=self.drop_photo)
        except Exception:
            pass
        result = read_qr(path)
        self._show_read_result(result)

    def _show_read_result(self, result):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        if result:
            self.result_text.insert("1.0", result)
            self.status_label.config(text=f"Decoded — {len(result)} characters found")
        else:
            self.result_text.insert("1.0", "No QR code found in image")
            self.status_label.config(text="Could not detect a QR code")
        self.result_text.config(state="disabled")

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp")])
        if not path:
            return
        self._load_image_file(path)

    def copy_result(self):
        self.result_text.config(state="normal")
        text = self.result_text.get("1.0", "end").strip()
        self.result_text.config(state="disabled")

        if text and text != "No QR code found in image":
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.copy_result_btn.config(text="Copied!")
            self.root.after(2000, lambda: self.copy_result_btn.config(text="Copy Result"))
        else:
            self.status_label.config(text="Nothing to copy")

if __name__ == "__main__":
    root = tk.Tk()
    app = QRToolApp(root)
    root.mainloop()
