from __future__ import annotations

from pathlib import Path

import zoom_recording_downloader as zrd


def test_normalize_filename_template_default() -> None:
    default = "%(title)s.%(ext)s"
    assert zrd.normalize_filename_template(None, default) == default


def test_normalize_filename_template_plain_name() -> None:
    default = "%(title)s.%(ext)s"
    assert zrd.normalize_filename_template("lecture_1", default) == "lecture_1.%(ext)s"


def test_normalize_filename_template_token_passthrough() -> None:
    default = "%(title)s.%(ext)s"
    value = "%(uploader)s_%(title)s.%(ext)s"
    assert zrd.normalize_filename_template(value, default) == value


def test_resolve_cookie_file_path_relative(monkeypatch, tmp_path: Path) -> None:
    fake_script = tmp_path / "zoom_recording_downloader.py"
    fake_script.write_text("", encoding="utf-8")
    monkeypatch.setattr(zrd, "__file__", str(fake_script))

    resolved = zrd.resolve_cookie_file_path("cookies.txt")
    assert resolved == tmp_path / "cookies" / "cookies.txt"


def test_resolve_cookie_file_path_absolute(tmp_path: Path) -> None:
    absolute = tmp_path / "x" / "cookies.txt"
    resolved = zrd.resolve_cookie_file_path(str(absolute))
    assert resolved == absolute


def test_get_default_cookie_file_path(monkeypatch, tmp_path: Path) -> None:
    fake_script = tmp_path / "zoom_recording_downloader.py"
    fake_script.write_text("", encoding="utf-8")
    monkeypatch.setattr(zrd, "__file__", str(fake_script))

    assert zrd.get_default_cookie_file_path() == tmp_path / "cookies" / "cookies.txt"


def test_next_available_path(tmp_path: Path) -> None:
    base = tmp_path / "video.mp4"
    base.write_text("x", encoding="utf-8")
    (tmp_path / "video (1).mp4").write_text("x", encoding="utf-8")

    next_path = zrd.next_available_path(base)
    assert next_path.name == "video (2).mp4"

