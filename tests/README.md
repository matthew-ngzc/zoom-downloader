# Test Suite Guide

This folder contains test suites for `zoom_recording_downloader.py`.

## How to run

```powershell
uv sync --dev
uv run pytest -q
```

Run everything in one command (static analysis + dependency audit + all tests including e2e):

```powershell
uv run python scripts/run_all_checks.py
```

Run only non-e2e tests:

```powershell
uv run pytest -m "not e2e" -q
```

Run e2e tests locally (after creating `.env` from `.env.example`):

```powershell
uv run pytest -m e2e -q
```

Run one specific test file (example: only public download e2e):

```powershell
uv run pytest -q tests/e2e/test_public_download_e2e.py
```

Run one specific test function:

```powershell
uv run pytest -q tests/e2e/test_public_download_e2e.py::test_public_download_e2e
```

Run tests by keyword expression (helpful for quick filtering):

```powershell
uv run pytest -q -k "public_download_e2e"
```

## What each test file covers

### `conftest.py`

- Adds the project root to `sys.path` so tests can import `zoom_recording_downloader.py` directly.

### `unit/test_paths.py`

- `normalize_filename_template(...)`
  - default handling
  - plain filename handling (`name` -> `name.%(ext)s`)
  - passthrough for templates already containing yt-dlp tokens
- `resolve_cookie_file_path(...)`
  - absolute path behavior
  - relative path behavior (resolved under `<script_dir>/cookies/...`)
- `get_default_cookie_file_path()`
  - default cookie path location
- `next_available_path(...)`
  - auto-increment naming (`(1)`, `(2)`, ...)

### `unit/test_prompts_and_menu.py`

- Prompt behavior:
  - required prompt re-prompt on blank
  - `exit` handling (`ExitRequested`)
  - `back` handling (`BackRequested`) for pre-download fields
- `collect_user_inputs()` flow:
  - supports moving back to previous field and re-entering values
- Post-download action menu:
  - fallback numeric mode behavior
  - arrow-key mode behavior (including selecting `See stack trace`)

### `unit/test_collision_and_errors.py`

- `looks_like_protected_recording_error(...)`
  - protected/auth-like errors are detected
  - unrelated errors are not falsely detected
- `resolve_outtmpl_with_collision_handling(...)`
  - no-conflict path
  - manual rename path
  - auto-number path when user presses Enter

### `integration/test_download_fallback.py`

- `download_zoom_recording(...)` protected-recording retry logic
  - first attempt without cookies fails
  - retry uses default `cookies/cookies.txt` when available
- verifies non-protected errors do not trigger cookie retry

### `e2e/test_public_download_e2e.py`

- Real public recording download e2e coverage (no cookies).

### `e2e/test_protected_cookie_b64_e2e.py`

- Protected recording e2e coverage using `E2E_ZOOM_COOKIES_TXT_B64`.

### `e2e/test_protected_passcode_refresh_e2e.py`

- Protected recording e2e coverage using passcode-based cookie refresh (`E2E_ZOOM_PROTECTED_PASSCODE`).

### `e2e/_helpers.py`

- Real download e2e coverage using external Zoom links:
  - shared env loading
  - env validation
  - error classification
  - downloaded-file assertions
- Uses environment variables (or local `.env`) so links/cookies are not committed.
- CI refreshes protected-recording cookies dynamically using Playwright + passcode before running e2e tests on release tags.
- Local protected e2e is configured to validate both paths in separate tests.
- E2E tests clean up downloaded files after each run to avoid disk buildup.
- Set `E2E_KEEP_ARTIFACTS=1` if you want to keep downloaded files for debugging.
- Adds explicit error prefixes in failure messages:
  - `E2E_CONFIG_ISSUE` for missing secret/config
  - `E2E_DATA_ISSUE` for likely deleted/expired/auth-cookie issues

## Scope notes

- The unit tests mock `yt_dlp` and do **not** perform real Zoom downloads.
- Only the e2e tests perform REAL zoom download checks, which are only ran before releases. 
