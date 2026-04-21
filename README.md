# Zoom Recording Downloader

This script downloads Zoom cloud recordings using `yt-dlp`.

## Password-Protected Videos

For password-protected Zoom recordings, the app now tries passcode-first automation:

1. You enter passcode in the interactive flow.
2. The app attempts automated auth and cookie refresh.
3. If that fails, it falls back to manual `cookies.txt` setup.

Use [Cookies Setup](#cookies-setup) only when passcode-first automation fails.

> This is safe as everything is happening on your machine, your passwords and cookies are not being sent anywhere (other than the Zoom server of course).

## Usage

There are 2 ways to run this app:

1. Download prebuilt release zip (no Python setup needed)
2. Clone and run from source code

### 1. Run from Release Zip (Recommended for non-technical users)

#### Requirements

- Windows or macOS
- Internet access (to reach Zoom recording URLs)

#### Steps:
1. Go to the `Releases` Section in this Github Repository
     ![Where to find Releases](images/releases.png)
2. Download the correct release asset for your OS/architecture:
   - `zoom-downloader-windows-x64.zip` (Windows)
   - `zoom-downloader-macos-arm64.zip` (Apple Silicon)
   - `zoom-downloader-macos-x64.zip` (Intel)

    ![Finding the correct file](images/files.png)
   
> [!CAUTION]
> Downloading and running executables carries inherent security risks.
> Only proceed if you explicitly trust the developer.
>
> You can **optionally verify the SHA-256 checksum** before running the binary. This does not affect its functionality.
> This is **strongly recommended**.
>
> OR you can avoid running the prebuilt binary entirely and build it yourself from source:
> [Run from Code](#2-run-from-code-clone)


3. (Optional, highly recommended) Verify the SHA-256 Hash
     Each release also includes matching checksum files. Download the one matching the `.zip` file you downloaded:
     - `zoom-downloader-windows-x64.zip.sha256`
     - `zoom-downloader-macos-arm64.zip.sha256`
     - `zoom-downloader-macos-x64.zip.sha256`
     
     Run the following command in a terminal from the directory containing both the `.zip` and `.sha256` files.
   
     Before running the command, open Terminal and change into the folder where both files were downloaded.
     For most users, this is usually `Downloads`. If you downloaded the files somewhere else, replace `~/Downloads` with that folder path.
     - Windows (PowerShell):
      ```powershell
      cd $HOME\Downloads
      $expected = (Get-Content .\zoom-downloader-windows-x64.zip.sha256).Split(" ")[0].ToLower()
      $actual = (Get-FileHash .\zoom-downloader-windows-x64.zip -Algorithm SHA256).Hash.ToLower()
      $expected -eq $actual
      ```
     
     - macOS (Apple Silicon):
      ```bash
      cd ~/Downloads
      shasum -a 256 -c zoom-downloader-macos-arm64.zip.sha256
      ```
      
     - macOS (Intel):
      ```bash
      cd ~/Downloads
      shasum -a 256 -c zoom-downloader-macos-x64.zip.sha256
      ```
     
     The check should report success (`True` on PowerShell, `OK` on macOS).

4. Extract the zip.

5. Open the extracted folder, then launch the app:
   - **Windows:** double-click `Run Zoom Downloader.bat`
   - **macOS:** double-click `Run Zoom Downloader.command`

For future runs, you only need to repeat step 5.
  

> [!NOTE]
> Release binaries are unsigned (macOS: not notarized, Windows: not code-signed), so first-run security warnings are expected.

> [!NOTE]
> **If blocked on macOS**
> - Open **System Settings -> Privacy & Security**.
> - Under Security, allow the blocked app, then run `Run Zoom Downloader.command` again.

> [!NOTE]
> **If blocked on Windows**
> - In SmartScreen, click **More info**.
> - Click **Run anyway**.

### 2. Run from Code (Clone)

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

If passcode-first automation fails for a protected recording, get `cookies.txt` and provide its path when prompted.

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

### 4. Optional: run release e2e tests locally

1. Copy `.env.example` to `.env`.
2. Fill these values in `.env`:
   - `E2E_ZOOM_PUBLIC_URL`
   - `E2E_ZOOM_PROTECTED_URL`
   - `E2E_ZOOM_PROTECTED_PASSCODE` (for passcode-refresh e2e path)
   - `E2E_ZOOM_COOKIES_TXT_B64` (for cookie-b64 e2e path)
3. Run:

```powershell
uv run pytest -m e2e -q
```

Build output is generated in:

- `dist/zoom-downloader.exe` (Windows)
- `build/` (PyInstaller build artifacts)

For release packaging, this repo's GitHub Actions workflow creates OS-specific zip bundles:

- `zoom-downloader-windows-x64.zip` includes `zoom-downloader.exe` + `Run Zoom Downloader.bat`.
- `zoom-downloader-macos-arm64.zip` includes `zoom-downloader` + `Run Zoom Downloader.command`.
- `zoom-downloader-macos-x64.zip` includes `zoom-downloader` + `Run Zoom Downloader.command`.
- Each zip has a corresponding `.sha256` file for integrity verification.

Release-tag CI (`v*`) also runs e2e tests using GitHub secrets:

- `E2E_ZOOM_PUBLIC_URL`
- `E2E_ZOOM_PROTECTED_URL`
- `E2E_ZOOM_PROTECTED_PASSCODE`

On release tags, CI uses Playwright to open the protected recording URL, submit passcode, and generate a fresh `cookies.txt` dynamically for e2e tests.  
You do not need to store `E2E_ZOOM_COOKIES_TXT_B64` in GitHub secrets for CI.

CI also includes:

- Static analysis: `ruff`
- Dependency vulnerability scan: `pip-audit`
- Secret scan: GitGuardian (`GITGUARDIAN_API_KEY` repository secret; scan is skipped with warning if not configured)

### 5. Trigger a release

Releases are triggered by pushing a git tag that starts with `v` (for example `v1.0.0`).

- Push to `main` (without tag): runs checks/tests/build, no GitHub Release publish.
- Push `v*` tag: runs release e2e + publish steps.

```powershell
git checkout main
git pull origin main
git tag v1.0.0
git push origin v1.0.0
```

If code is already committed locally, you can push code + tag in one shot:

```powershell
git push origin main v1.0.0
```

If code is already on remote `main` and you only want to release that commit, push only the tag:

```powershell
git push origin v1.0.0
```

If you need to move a mistaken tag:

```powershell
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

# TODOS
- explore TUI with Textual
- add more cicd stuff
  - [ ] dependabot
  - [ ] codeql
  - [ ] zizmor (github actions security checker)
