# Test Suite Guide

This folder contains unit tests for `zoom_recording_downloader.py`.

## How to run

```powershell
uv sync --dev
uv run pytest -q
```

## What each test file covers

### `conftest.py`

- Adds the project root to `sys.path` so tests can import `zoom_recording_downloader.py` directly.

### `test_paths.py`

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

### `test_prompts_and_menu.py`

- Prompt behavior:
  - required prompt re-prompt on blank
  - `exit` handling (`ExitRequested`)
  - `back` handling (`BackRequested`) for pre-download fields
- `collect_user_inputs()` flow:
  - supports moving back to previous field and re-entering values
- Post-download action menu:
  - fallback numeric mode behavior
  - arrow-key mode behavior (including selecting `See stack trace`)

### `test_collision_and_errors.py`

- `looks_like_protected_recording_error(...)`
  - protected/auth-like errors are detected
  - unrelated errors are not falsely detected
- `resolve_outtmpl_with_collision_handling(...)`
  - no-conflict path
  - manual rename path
  - auto-number path when user presses Enter

### `test_download_fallback.py`

- `download_zoom_recording(...)` protected-recording retry logic
  - first attempt without cookies fails
  - retry uses default `cookies/cookies.txt` when available
- verifies non-protected errors do not trigger cookie retry

## Scope notes

- These tests are unit tests with mocks/stubs for `yt_dlp`.
- They do **not** perform real Zoom downloads.
- Real download checks are better treated as integration/e2e smoke tests, usually run manually or in a separate optional CI workflow.
