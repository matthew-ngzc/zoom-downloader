from __future__ import annotations

from pathlib import Path

import zoom_recording_downloader as zrd


def test_looks_like_protected_recording_error_true() -> None:
    err = Exception("ERROR: No video formats found! password required")
    assert zrd.looks_like_protected_recording_error(err) is True


def test_looks_like_protected_recording_error_false() -> None:
    err = Exception("network timeout while connecting")
    assert zrd.looks_like_protected_recording_error(err) is False


def test_resolve_outtmpl_with_collision_no_conflict(monkeypatch, tmp_path: Path) -> None:
    url = "https://zoom.us/rec/play/abc"
    output_dir = tmp_path
    template = "%(title)s.%(ext)s"
    monkeypatch.setattr(zrd, "predict_output_path", lambda *_args: None)

    outtmpl = zrd.resolve_outtmpl_with_collision_handling(url, output_dir, template, None)
    assert outtmpl == str(output_dir / template)


def test_resolve_outtmpl_with_collision_manual_name(monkeypatch, tmp_path: Path) -> None:
    url = "https://zoom.us/rec/play/abc"
    output_dir = tmp_path
    template = "%(title)s.%(ext)s"
    existing = output_dir / "existing.mp4"
    existing.write_text("x", encoding="utf-8")

    monkeypatch.setattr(zrd, "predict_output_path", lambda *_args: existing)
    monkeypatch.setattr(zrd, "prompt_optional", lambda *_args, **_kwargs: "new_file")

    outtmpl = zrd.resolve_outtmpl_with_collision_handling(url, output_dir, template, None)
    assert outtmpl == str(output_dir / "new_file.mp4")


def test_resolve_outtmpl_with_collision_auto_number(monkeypatch, tmp_path: Path) -> None:
    url = "https://zoom.us/rec/play/abc"
    output_dir = tmp_path
    template = "%(title)s.%(ext)s"
    existing = output_dir / "existing.mp4"
    existing.write_text("x", encoding="utf-8")

    monkeypatch.setattr(zrd, "predict_output_path", lambda *_args: existing)
    monkeypatch.setattr(zrd, "prompt_optional", lambda *_args, **_kwargs: None)

    outtmpl = zrd.resolve_outtmpl_with_collision_handling(url, output_dir, template, None)
    assert outtmpl == str(output_dir / "existing (1).mp4")

