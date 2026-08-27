# DocAuthorize

Desktop application (Python + PySide6) for automated processing of contracts, annexes, and other PDF documents. Built for authorizing and tracking client documents, generating reports, and managing document history.

## Features

- Import single or batch PDF documents
- Automatic data extraction from PDFs (text extraction via PyMuPDF/pdfplumber, OCR support via Tesseract)
- Document authorization and verification workflow (email-based verification codes)
- Client history tracking with searchable records
- Export reports to Excel (.xlsx)
- Automatic database backups
- English / Polish user interface
- SQLite database storage

## Requirements

- Python 3.9 or newer (developed and tested on Python 3.12)
- Tesseract OCR engine (system-level install, required by `pytesseract`)
- See `requirements.txt` for Python package dependencies

## Project Structure

```
DocAuthorize/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── backend/
│   ├── database/                # SQLite database and access layer (db.py)
│   ├── gui/                     # PySide6 interface, splash screen, styles
│   ├── reports/                 # Generated Excel reports
│   ├── services/                # PDF reading, OCR, export logic
│   └── translations/            # EN/PL language files (english.py, polish.py, manager.py)
├── backups/                     # Automatic timestamped database backups
└── docauthorize.db              # Main SQLite database
```

## Installation

### macOS

```bash
git clone https://github.com/duskrosee/DocAuthorize.git
cd DocAuthorize
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install Tesseract OCR (required for `pytesseract`):

```bash
brew install tesseract
```

### Windows

```powershell
git clone https://github.com/duskrosee/DocAuthorize.git
cd DocAuthorize
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Install Tesseract OCR:
1. Download the installer from [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer and note the install path (usually `C:\Program Files\Tesseract-OCR`)
3. Add that path to your system `PATH`, or set it directly in the app settings/code (`pytesseract.pytesseract.tesseract_cmd`)

### Linux (Debian/Ubuntu)

```bash
git clone https://github.com/duskrosee/DocAuthorize.git
cd DocAuthorize
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo apt install tesseract-ocr
```

## Running the App

Activate your virtual environment first, then:

```bash
python main.py
```

## Database

The app uses SQLite by default (`docauthorize.db`). Automatic backups are saved to the `backups/` folder with a timestamp on each save (e.g. `backup_2026-08-26_17-32-46.db`).

## Email / Verification

The app can send verification codes and reports via SMTP. Configure sender email, password, and recipient in the app's Settings screen. For providers requiring app passwords (Gmail, Outlook/Office 365 with 2FA enabled), generate an app-specific password from your email provider's security settings rather than using your regular login password.

## Localization

The interface supports English and Polish, defined in `backend/translations/english.py` and `backend/translations/polish.py`. Language switching is handled by `backend/translations/manager.py`.

## Building a Standalone Executable

To package the app as a standalone executable (`.exe` on Windows, `.app` on macOS), use PyInstaller. Note that PyInstaller must be run on the target OS — a Windows `.exe` must be built on Windows, and a macOS app must be built on macOS.

```bash
pip install pyinstaller
pyinstaller --name DocAuthorize --windowed --onefile main.py
```

Adjust `--add-data` flags as needed to bundle the `backend/translations` folder and any other non-Python resource files.

## License

Internal / private project — not currently published under an open-source license
