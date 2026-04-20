# Zoom Recorder Downloader

This script downloads Zoom cloud recordings using `yt-dlp`.

## Password-Protected Videos

For password-protected Zoom recordings, this project uses `cookies.txt` instead of passcode input.  
Passcode-only extraction is not reliable here; use [Cookies Setup](#cookies-setup).

## Usage

There are 2 ways to run this app:

1. Download prebuilt release zip (no Python setup needed)
2. Clone and run from source code

### Run from Release Zip

#### Requirements

- Windows or macOS
- Internet access (to reach Zoom recording URLs)

#### Steps

- Download the correct release asset for your OS/architecture:
  - `zoom-downloader-windows-x64.zip`
  - `zoom-downloader-macos-arm64.zip` (Apple Silicon)
  - `zoom-downloader-macos-x64.zip` (Intel)
- Extract the zip.
- Run the launcher:
  - Windows: `Run Zoom Downloader.bat`
  - macOS: `Run Zoom Downloader.command`

#### macOS note

- These binaries are not notarized. macOS may show a security warning on first run.
- If blocked, allow it in System Settings -> Privacy & Security, then run again.

### Run from Code (Clone)

#### Requirements

- Windows/macOS/Linux with terminal access
- Python 3.10 or newer
- `uv` installed
- Internet access (to reach Zoom recording URLs)

#### Steps

```powershell
git clone https://github.com/matthew-ngzc/zoom-downloader.git
cd zoom-downloader
uv venv
uv sync
uv run python zoom_recording_downloader.py
```

## Cookies Setup

For password-protected recordings, get `cookies.txt` and provide its path in the script prompt.

- Install **Get cookies.txt LOCALLY**:  
  https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Open the Zoom recording page in your browser and make sure it is unlocked/playable.
- Export cookies in Netscape format and save as `cookies.txt`.
  ![How to export cookies](images/export_cookies.png)
- When prompted for `Cookies file path`, you can use:
- Relative filename, e.g. `cookies.txt` (resolved to `<project>/zoom_recorder/cookies/cookies.txt`)
- Relative path, e.g. `archive/cookies2.txt` (resolved to `<project>/zoom_recorder/cookies/archive/cookies2.txt`)
- Absolute path, e.g. `C:\Users\yourname\Downloads\cookies.txt`
- If you leave cookie path blank and the recording appears protected, the script auto-retries with `zoom_recorder/cookies/cookies.txt` when that file exists.

## Developer Notes

### 1. Install dev dependencies

```powershell
uv sync --dev
```

### 2. Run locally (dev)

```powershell
uv run python zoom_recording_downloader.py
```

### 3. Build executable (PyInstaller + spec)

```powershell
uv run pyinstaller --noconfirm --clean zoom-downloader.spec
```

Build output is generated in:

- `dist/zoom-downloader.exe` (Windows)
- `build/` (PyInstaller build artifacts)

For release packaging, this repo's GitHub Actions workflow creates OS-specific zip bundles:

- `zoom-downloader-windows-x64.zip` includes `zoom-downloader.exe` + `Run Zoom Downloader.bat`.
- `zoom-downloader-macos-arm64.zip` includes `zoom-downloader` + `Run Zoom Downloader.command`.
- `zoom-downloader-macos-x64.zip` includes `zoom-downloader` + `Run Zoom Downloader.command`.
