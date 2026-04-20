from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from yt_dlp.utils import DownloadError

import zoom_recording_downloader as zrd


def test_download_retries_with_default_cookies(monkeypatch, tmp_path: Path) -> None:
    fake_script = tmp_path / "zoom_recording_downloader.py"
    fake_script.write_text("", encoding="utf-8")
    monkeypatch.setattr(zrd, "__file__", str(fake_script))

    default_cookie = tmp_path / "cookies" / "cookies.txt"
    default_cookie.parent.mkdir(parents=True, exist_ok=True)
    default_cookie.write_text("cookie", encoding="utf-8")

    monkeypatch.setattr(
        zrd,
        "resolve_outtmpl_with_collision_handling",
        lambda *_args: str(tmp_path / "out.%(ext)s"),
    )

    call_cookiefiles: list[str | None] = []

    class FakeYDL:
        def __init__(self, opts: dict[str, Any]) -> None:
            self.opts = opts

        def __enter__(self) -> "FakeYDL":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def download(self, _urls: list[str]) -> None:
            cookiefile = self.opts.get("cookiefile")
            call_cookiefiles.append(cookiefile)
            if cookiefile is None:
                raise DownloadError("No video formats found")

    monkeypatch.setattr(zrd.yt_dlp, "YoutubeDL", FakeYDL)

    zrd.download_zoom_recording(
        url="https://zoom.us/rec/play/abc",
        output_dir=tmp_path / "downloads",
        filename_template="%(title)s.%(ext)s",
        cookie_file_path=None,
    )

    assert len(call_cookiefiles) == 2
    assert call_cookiefiles[0] is None
    assert call_cookiefiles[1] == str(default_cookie)


def test_download_no_retry_when_not_protected(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        zrd,
        "resolve_outtmpl_with_collision_handling",
        lambda *_args: str(tmp_path / "out.%(ext)s"),
    )

    class FakeYDL:
        def __init__(self, _opts: dict[str, Any]) -> None:
            pass

        def __enter__(self) -> "FakeYDL":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def download(self, _urls: list[str]) -> None:
            raise DownloadError("connection reset by peer")

    monkeypatch.setattr(zrd.yt_dlp, "YoutubeDL", FakeYDL)

    with pytest.raises(DownloadError):
        zrd.download_zoom_recording(
            url="https://zoom.us/rec/play/abc",
            output_dir=tmp_path / "downloads",
            filename_template="%(title)s.%(ext)s",
            cookie_file_path=None,
        )

