from __future__ import annotations

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


def test_e2e_public_recording_download(tmp_path: Path) -> None:
    load_local_env()
    url = required_env("E2E_ZOOM_PUBLIC_URL")
    output_dir = tmp_path / "public"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        try:
            zrd.download_zoom_recording(
                url=url,
                output_dir=output_dir,
                filename_template="%(title)s.%(ext)s",
                cookie_file_path=None,
            )
        except DownloadError as exc:
            data_issue = classify_data_issue(exc)
            if data_issue:
                pytest.fail(f"E2E_DATA_ISSUE: public recording test failed: {data_issue}")
            raise

        files = assert_any_media_downloaded(output_dir)
        log_masked_downloaded_files(files)
    finally:
        cleanup_output_dir(tmp_path)
