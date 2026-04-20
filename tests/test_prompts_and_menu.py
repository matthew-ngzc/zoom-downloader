from __future__ import annotations

import types
from collections import deque
from pathlib import Path

import pytest

import zoom_recording_downloader as zrd


def test_prompt_required_reprompts_blank(monkeypatch) -> None:
    inputs = iter(["", "https://example.com"])
    monkeypatch.setattr(zrd, "clear_input_buffer", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    assert zrd.prompt_required("URL: ") == "https://example.com"


def test_prompt_required_exit(monkeypatch) -> None:
    monkeypatch.setattr(zrd, "clear_input_buffer", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: "exit")
    with pytest.raises(zrd.ExitRequested):
        zrd.prompt_required("URL: ")


def test_prompt_optional_back(monkeypatch) -> None:
    monkeypatch.setattr(zrd, "clear_input_buffer", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: "back")
    with pytest.raises(zrd.BackRequested):
        zrd.prompt_optional("Filename: ", allow_back=True)


def test_collect_user_inputs_with_back(monkeypatch, tmp_path: Path) -> None:
    fake_script = tmp_path / "zoom_recording_downloader.py"
    fake_script.write_text("", encoding="utf-8")
    monkeypatch.setattr(zrd, "__file__", str(fake_script))
    monkeypatch.setattr(zrd, "clear_input_buffer", lambda: None)
    monkeypatch.setattr(zrd, "print_output_folder_help", lambda *_args: None)
    monkeypatch.setattr(zrd, "print_cookies_help", lambda *_args: None)

    # URL -> Output -> back at Filename -> Output (again) -> Filename -> Cookies
    inputs = iter(
        [
            "https://zoom.us/rec/play/abc",
            "downloads_a",
            "back",
            "downloads_b",
            "custom_name",
            "cookies.txt",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    url, output_dir, filename_template, cookie_file = zrd.collect_user_inputs()

    assert url == "https://zoom.us/rec/play/abc"
    assert output_dir.name == "downloads_b"
    assert filename_template == "custom_name.%(ext)s"
    assert cookie_file == tmp_path / "cookies" / "cookies.txt"


def test_prompt_next_action_fallback_numeric(monkeypatch) -> None:
    monkeypatch.setattr(zrd, "clear_input_buffer", lambda: None)
    monkeypatch.setattr(zrd, "supports_ansi", lambda: False)

    # Force fallback branch by throwing on import msvcrt usage.
    class _BadModule:
        def __getattr__(self, _name: str):
            raise RuntimeError("no msvcrt")

    monkeypatch.setitem(__import__("sys").modules, "msvcrt", _BadModule())
    inputs = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    action = zrd.prompt_next_action(download_succeeded=True, allow_stack_trace=False)
    assert action == "close"


def test_prompt_next_action_arrow_mode_trace(monkeypatch) -> None:
    monkeypatch.setattr(zrd, "clear_input_buffer", lambda: None)
    monkeypatch.setattr(zrd, "supports_ansi", lambda: False)

    keys = deque([b"\xe0", b"P", b"\xe0", b"P", b"\r"])  # down, down, enter -> option 3

    fake_msvcrt = types.SimpleNamespace(
        getch=lambda: keys.popleft(),
        kbhit=lambda: False,
        getwch=lambda: "",
    )
    monkeypatch.setitem(__import__("sys").modules, "msvcrt", fake_msvcrt)

    action = zrd.prompt_next_action(download_succeeded=False, allow_stack_trace=True)
    assert action == "trace"

