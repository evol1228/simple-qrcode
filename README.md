# QR Tool

A lightweight desktop QR code generator and reader built with Python and tkinter.

## Features

- **Generate QR codes** — Type text or a URL and get a live QR preview
- **Save as PNG** — Export QR codes to image files
- **Read QR codes** — Load any image and decode the QR content
- **Copy to clipboard** — One-click copy for both input and decoded results
- **Tabbed interface** — Clean Generate/Read tabs

## Requirements

| Dependency | Install |
|------------|---------|
| Python 3.6+ | [python.org](https://python.org) |
| tkinter | Included (Linux: `sudo apt install python3-tk`) |
| qrcode | `pip install -r requirements.txt` |
| Pillow | `pip install -r requirements.txt` |
| pyzbar | `pip install -r requirements.txt` |

**Note:** pyzbar requires the ZBar shared library. On Windows it's bundled. On Linux: `sudo apt install libzbar0`

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
   ```bash
   python qr_tool.py
   ```

2. **Generate tab** — Type or paste text/URL, QR updates live. Save or copy.

3. **Read tab** — Click "Open Image", select a QR code image, get the decoded text.

## Building

To compile to a standalone executable (optional):

```bash
pip install nuitka
python -m nuitka --standalone --onefile --windows-disable-console qr_tool.py
```

## License

MIT
