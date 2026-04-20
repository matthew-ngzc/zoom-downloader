from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError

import zoom_recording_downloader as zrd
from tests.e2e._helpers import (
    assert_any_media_downloaded,
    classify_data_issue,
    cleanup_output_dir,
    load_local_env,
    log_masked_downloaded_files,
    required_env,
)

pytestmark = pytest.mark.e2e


def test_e2e_protected_recording_download_with_cookie_b64(tmp_path: Path) -> None:
    load_local_env()
    url = required_env("E2E_ZOOM_PROTECTED_URL")
    cookies_b64 = os.getenv("E2E_ZOOM_COOKIES_TXT_B64", "").strip()
    if not cookies_b64:
        pytest.skip("E2E_ZOOM_COOKIES_TXT_B64 is not set; skipping cookie-b64 e2e test.")
    output_dir = tmp_path / "protected-cookie-b64"
    output_dir.mkdir(parents=True, exist_ok=True)

    cookie_file = output_dir / "cookies.txt"
    cookie_file.write_bytes(base64.b64decode(cookies_b64))

    try:
        try:
            zrd.download_zoom_recording(
                url=url,
                output_dir=output_dir,
                filename_template="%(title)s.%(ext)s",
                cookie_file_path=cookie_file,
            )
        except DownloadError as exc:
            data_issue = classify_data_issue(exc)
            if data_issue:
                pytest.fail(f"E2E_DATA_ISSUE: protected recording (cookie-b64) test failed: {data_issue}")
            raise

        files = assert_any_media_downloaded(output_dir, excludes={"cookies.txt"})
        log_masked_downloaded_files(files)
    finally:
        cleanup_output_dir(tmp_path)
