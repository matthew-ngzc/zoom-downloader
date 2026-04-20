from __future__ import annotations

from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError

from scripts.refresh_zoom_cookies import refresh_zoom_cookies
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


def test_e2e_protected_recording_download_with_passcode_refresh(tmp_path: Path) -> None:
    load_local_env()
    url = required_env("E2E_ZOOM_PROTECTED_URL")
    passcode = required_env("E2E_ZOOM_PROTECTED_PASSCODE")
    output_dir = tmp_path / "protected-passcode-refresh"
    output_dir.mkdir(parents=True, exist_ok=True)

    cookie_file = output_dir / "cookies.txt"
    refresh_zoom_cookies(url, passcode, cookie_file)

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
                pytest.fail(
                    "E2E_DATA_ISSUE: protected recording (passcode refresh) test failed: "
                    f"{data_issue}"
                )
            raise

        files = assert_any_media_downloaded(output_dir, excludes={"cookies.txt"})
        log_masked_downloaded_files(files)
    finally:
        cleanup_output_dir(tmp_path)
