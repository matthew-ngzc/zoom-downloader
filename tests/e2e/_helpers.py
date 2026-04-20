from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".m4v",
    ".avi",
    ".flv",
    ".ts",
}


def load_local_env() -> None:
    """Minimal .env loader for local runs (no extra dependency needed).

    Local `.env` values overwrite existing environment variables by default.
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    pytest.fail(f"E2E_CONFIG_ISSUE: Missing required secret/env var: {name}")


def classify_data_issue(exc: DownloadError) -> str | None:
    msg = str(exc).lower()
    indicators = (
        "no video formats found",
        "unable to extract",
        "not found",
        "deleted",
        "private",
        "forbidden",
        "403",
        "401",
        "cookie",
        "passcode",
        "password",
    )
    if any(indicator in msg for indicator in indicators):
        return str(exc)
    return None


def _mask_filename(filename: str) -> tuple[str, str]:
    path = Path(filename)
    stem = path.stem
    ext = path.suffix
    if len(stem) <= 6:
        masked_stem = stem
    else:
        middle_len = len(stem) - 6
        masked_stem = f"{stem[:3]}{'*' * middle_len}{stem[-3:]}"
    return masked_stem, ext


def find_downloaded_videos(output_dir: Path, *, excludes: set[str] | None = None) -> list[Path]:
    excludes = excludes or set()
    files = [
        p
        for p in output_dir.iterdir()
        if (
            p.is_file()
            and p.name not in excludes
            and p.stat().st_size > 0
            and p.suffix.lower() in VIDEO_EXTENSIONS
        )
    ]
    return files


def assert_any_media_downloaded(output_dir: Path, *, excludes: set[str] | None = None) -> list[Path]:
    files = find_downloaded_videos(output_dir, excludes=excludes)
    assert files, (
        "Expected at least one downloaded video file with a video extension "
        f"{sorted(VIDEO_EXTENSIONS)}"
    )
    return files


def log_masked_downloaded_files(files: list[Path]) -> None:
    for file in files:
        masked_stem, ext = _mask_filename(file.name)
        print(f'Downloaded: "{masked_stem}"{ext}')


def cleanup_output_dir(output_dir: Path) -> None:
    keep = os.getenv("E2E_KEEP_ARTIFACTS", "").strip().lower() in {"1", "true", "yes", "on"}
    if not keep:
        shutil.rmtree(output_dir, ignore_errors=True)
