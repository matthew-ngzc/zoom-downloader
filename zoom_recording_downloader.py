#!/usr/bin/env python3
"""Download a Zoom cloud recording URL using yt-dlp (interactive mode)."""

from __future__ import annotations

import os
import sys
import time
import ctypes
from pathlib import Path
from typing import Any, cast

import yt_dlp
from yt_dlp.utils import DownloadError

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_ENABLED = False


def configure_console_output() -> None:
    global ANSI_ENABLED
    # Ensure Unicode block-art headers render correctly on Windows terminals.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    # Enable ANSI escape processing on Windows consoles when possible.
    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                if kernel32.SetConsoleMode(handle, new_mode):
                    ANSI_ENABLED = True
        except Exception:
            pass
    if not ANSI_ENABLED:
        ANSI_ENABLED = sys.stdout.isatty() or bool(os.getenv("FORCE_COLOR"))


def supports_ansi() -> bool:
    if os.getenv("FORCE_COLOR"):
        return True
    if os.getenv("NO_COLOR"):
        return False
    return ANSI_ENABLED


def supports_truecolor() -> bool:
    if os.getenv("FORCE_TRUECOLOR"):
        return True
    colorterm = (os.getenv("COLORTERM") or "").lower()
    if "truecolor" in colorterm or "24bit" in colorterm:
        return True
    # Common Windows terminals with truecolor support.
    if os.getenv("WT_SESSION") or (os.getenv("TERM_PROGRAM") or "").lower() == "vscode":
        return True
    return False


def colorize(text: str, color_code: str, *, bold: bool = False) -> str:
    if not supports_ansi():
        return text
    style = ANSI_BOLD if bold else ""
    return f"{style}\033[{color_code}m{text}{ANSI_RESET}"


def colorize_rgb(
    text: str,
    rgb: tuple[int, int, int],
    *,
    bold: bool = False,
    fallback_code: str = "37",
) -> str:
    if not supports_ansi():
        return text
    if not supports_truecolor():
        return colorize(text, fallback_code, bold=bold)
    style = ANSI_BOLD if bold else ""
    r, g, b = rgb
    return f"{style}\033[38;2;{r};{g};{b}m{text}{ANSI_RESET}"


def gradient_text(text: str) -> str:
    if not supports_ansi():
        return text
    if not supports_truecolor():
        return colorize(text, "96", bold=True)
    # Blue -> Cyan gradient using ANSI truecolor.
    start_r, start_g, start_b = 58, 123, 213
    end_r, end_g, end_b = 0, 212, 255
    length = max(len(text) - 1, 1)
    colored_chars: list[str] = []
    for idx, char in enumerate(text):
        ratio = idx / length
        r = int(start_r + (end_r - start_r) * ratio)
        g = int(start_g + (end_g - start_g) * ratio)
        b = int(start_b + (end_b - start_b) * ratio)
        colored_chars.append(f"\033[38;2;{r};{g};{b}m{char}")
    return "".join(colored_chars) + ANSI_RESET


def gradient_text_custom(
    text: str,
    start_rgb: tuple[int, int, int],
    end_rgb: tuple[int, int, int],
) -> str:
    if not supports_ansi():
        return text
    if not supports_truecolor():
        return colorize(text, "96")
    start_r, start_g, start_b = start_rgb
    end_r, end_g, end_b = end_rgb
    length = max(len(text) - 1, 1)
    colored_chars: list[str] = []
    for idx, char in enumerate(text):
        ratio = idx / length
        r = int(start_r + (end_r - start_r) * ratio)
        g = int(start_g + (end_g - start_g) * ratio)
        b = int(start_b + (end_b - start_b) * ratio)
        colored_chars.append(f"\033[38;2;{r};{g};{b}m{char}")
    return "".join(colored_chars) + ANSI_RESET


def ui_section(text: str) -> str:
    return colorize_rgb(text, (120, 205, 255), bold=True, fallback_code="96")


def ui_prompt(text: str) -> str:
    return colorize_rgb(text, (255, 214, 135), bold=True, fallback_code="93")


def ui_example(text: str) -> str:
    return colorize_rgb(text, (130, 225, 185), fallback_code="92")


def ui_default(text: str) -> str:
    return colorize_rgb(text, (185, 185, 185), fallback_code="90")


def ui_warning(text: str) -> str:
    return colorize_rgb(text, (255, 165, 110), bold=True, fallback_code="33")


def ui_error(text: str) -> str:
    return colorize_rgb(text, (255, 105, 105), bold=True, fallback_code="91")


def colorize_log_tag(tag: str) -> str:
    tag_lower = tag.lower()
    if tag_lower == "download":
        return colorize_rgb(f"[{tag}]", (130, 225, 185), bold=True, fallback_code="92")
    if tag_lower == "info":
        return colorize_rgb(f"[{tag}]", (120, 205, 255), bold=True, fallback_code="96")
    if tag_lower in {"debug"}:
        return colorize_rgb(f"[{tag}]", (170, 170, 170), fallback_code="90")
    if tag_lower in {"warning"}:
        return colorize_rgb(f"[{tag}]", (255, 180, 110), bold=True, fallback_code="33")
    if tag_lower in {"error"}:
        return colorize_rgb(f"[{tag}]", (255, 105, 105), bold=True, fallback_code="91")
    # Extractor / site tags like [zoom], [generic], [youtube]
    return colorize_rgb(f"[{tag}]", (110, 170, 255), bold=True, fallback_code="94")


def colorize_ydlp_message(msg: str) -> str:
    if msg.startswith("[") and "]" in msg:
        end = msg.find("]")
        tag = msg[1:end]
        remainder = msg[end + 1 :]
        return f"{colorize_log_tag(tag)}{remainder}"
    return msg


class YtDlpColorLogger:
    def __init__(self, progress_renderer: "DownloadProgressRenderer") -> None:
        self.progress_renderer = progress_renderer

    def _print_normal(self, msg: str) -> None:
        self.progress_renderer.finish_line_if_active()
        print(colorize_ydlp_message(msg))

    def debug(self, msg: str) -> None:
        # yt-dlp routes many normal lines through debug().
        # Progress lines are handled by progress_hooks to guarantee in-place updates.
        if msg.startswith("[download]") and ("% of" in msg or "ETA" in msg):
            return
        self._print_normal(msg)

    def info(self, msg: str) -> None:
        if msg.startswith("[download]") and ("% of" in msg or "ETA" in msg):
            return
        self._print_normal(msg)

    def warning(self, msg: str) -> None:
        self.progress_renderer.finish_line_if_active()
        print(ui_warning(colorize_ydlp_message(msg)))

    def error(self, msg: str) -> None:
        self.progress_renderer.finish_line_if_active()
        print(ui_error(colorize_ydlp_message(msg)))


class DownloadProgressRenderer:
    def __init__(self) -> None:
        self.active = False
        self.start_time: float | None = None
        self.last_plain_len = 0

    def _format_bytes(self, value: float | int | None) -> str:
        if value is None:
            return "Unknown"
        num = float(value)
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        unit_idx = 0
        while num >= 1024 and unit_idx < len(units) - 1:
            num /= 1024
            unit_idx += 1
        if unit_idx == 0:
            return f"{int(num)}B"
        return f"{num:,.2f}{units[unit_idx]}".replace(",", "")

    def _format_eta(self, value: int | float | None) -> str:
        if value is None:
            return "Unknown"
        total_seconds = max(0, int(value))
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02}:{seconds:02}"

    def _format_elapsed_hms(self, value: int | float | None) -> str:
        if value is None:
            return "00:00:00"
        total_seconds = max(0, int(value))
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def _color_with_progress(
        self,
        text: str,
        percent: float,
        *,
        start_rgb: tuple[int, int, int],
        end_rgb: tuple[int, int, int],
        fallback_low: str,
        fallback_mid: str,
        fallback_high: str,
        bold: bool = True,
    ) -> str:
        pct = max(0.0, min(100.0, percent)) / 100.0
        if supports_truecolor():
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * pct)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * pct)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * pct)
            return colorize_rgb(text, (r, g, b), bold=bold, fallback_code=fallback_high)
        if pct < 0.34:
            return colorize(text, fallback_low, bold=bold)
        if pct < 0.67:
            return colorize(text, fallback_mid, bold=bold)
        return colorize(text, fallback_high, bold=bold)

    def finish_line_if_active(self) -> None:
        if self.active:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.active = False
            self.last_plain_len = 0

    def _render_inline(self, plain_line: str, display_line: str, *, final: bool) -> None:
        if supports_ansi():
            sys.stdout.write("\033[2K\r" + display_line)
        else:
            padding = " " * max(0, self.last_plain_len - len(plain_line))
            sys.stdout.write("\r" + display_line + padding)
        if final:
            sys.stdout.write("\n")
            self.active = False
            self.last_plain_len = 0
        else:
            self.active = True
            self.last_plain_len = len(plain_line)
        sys.stdout.flush()

    def hook(self, status: dict[str, Any]) -> None:
        state = status.get("status")
        if state == "downloading":
            if self.start_time is None:
                self.start_time = time.monotonic()
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            downloaded = status.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100.0) if total else 0.0
            total_str = self._format_bytes(total)
            speed = status.get("speed")
            speed_str = f"{self._format_bytes(speed)}/s" if speed else "Unknown B/s"
            eta_str = self._format_eta(status.get("eta"))
            elapsed = status.get("elapsed")
            if elapsed is None and self.start_time is not None:
                elapsed = time.monotonic() - self.start_time
            elapsed_str = self._format_elapsed_hms(elapsed)
            percent_str = f"{percent:5.1f}%"
            plain_line = (
                f"[download] {percent:5.1f}% of {total_str} "
                f"in {elapsed_str} at {speed_str} ETA {eta_str}"
            )
            display_line = (
                f"{self._color_with_progress('[download]', percent, start_rgb=(220, 70, 70), end_rgb=(90, 230, 120), fallback_low='91', fallback_mid='93', fallback_high='92')} "
                f"{self._color_with_progress(percent_str, percent, start_rgb=(60, 120, 165), end_rgb=(140, 240, 255), fallback_low='36', fallback_mid='96', fallback_high='96')} of "
                f"{self._color_with_progress(total_str, percent, start_rgb=(70, 120, 90), end_rgb=(150, 255, 180), fallback_low='32', fallback_mid='92', fallback_high='92')} in "
                f"{self._color_with_progress(elapsed_str, percent, start_rgb=(100, 70, 130), end_rgb=(230, 130, 255), fallback_low='35', fallback_mid='95', fallback_high='95')} at "
                f"{self._color_with_progress(speed_str, percent, start_rgb=(120, 100, 60), end_rgb=(255, 225, 120), fallback_low='33', fallback_mid='93', fallback_high='93')} ETA "
                f"{self._color_with_progress(eta_str, percent, start_rgb=(100, 70, 130), end_rgb=(230, 130, 255), fallback_low='35', fallback_mid='95', fallback_high='95')}"
            )
            self._render_inline(plain_line, display_line, final=False)
        elif state == "finished":
            total = (
                status.get("total_bytes")
                or status.get("downloaded_bytes")
                or status.get("total_bytes_estimate")
            )
            elapsed = status.get("elapsed")
            if elapsed is None and self.start_time is not None:
                elapsed = time.monotonic() - self.start_time
            speed = status.get("speed")
            if (not speed or speed <= 0) and elapsed and total:
                speed = total / elapsed
            total_str = self._format_bytes(total)
            elapsed_str = self._format_elapsed_hms(elapsed)
            speed_str = f"{self._format_bytes(speed)}/s" if speed else "Unknown B/s"
            plain_line = f"[download] 100% of {total_str} in {elapsed_str} at {speed_str}"
            display_line = (
                f"{colorize_log_tag('download')} "
                f"{colorize('100%', '96', bold=True)} of "
                f"{colorize(total_str, '92', bold=True)} in "
                f"{colorize(elapsed_str, '95', bold=True)} at "
                f"{colorize(speed_str, '93', bold=True)}"
            )
            self._render_inline(plain_line, display_line, final=True)


def print_zoom_downloader_header() -> None:
    lines = [
        "███████╗ ██████╗  ██████╗ ███╗   ███╗   ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  █████╗ ██████╗ ███████╗██████╗",
        "╚══███╔╝██╔═══██╗██╔═══██╗████╗ ████║   ██╔══██╗██╔═══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗",
        "  ███╔╝ ██║   ██║██║   ██║██╔████╔██║   ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║███████║██║  ██║█████╗  ██████╔╝",
        " ███╔╝  ██║   ██║██║   ██║██║╚██╔╝██║   ██║  ██║██║   ██║██║███╗██║██║╚██╗██║██║     ██║   ██║██╔══██║██║  ██║██╔══╝  ██╔══██╗",
        "███████╗╚██████╔╝╚██████╔╝██║ ╚═╝ ██║   ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝██║  ██║██████╔╝███████╗██║  ██║",
        "╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝   ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝",
    ]
    separator = gradient_text("=" * max(len(line) for line in lines))
    print(separator)
    for line in lines:
        print(colorize(line, "94", bold=True))
    print(
        gradient_text_custom(
            "Interactive yt-dlp helper",
            (0, 200, 255),
            (0, 255, 160),
        )
    )
    if supports_ansi():
        print(
            f"{gradient_text_custom('Created by: ', (255, 190, 0), (255, 120, 0))}"
            f"{colorize('matthew-ngzc', '95', bold=True)}"
        )
    else:
        print("Created by: matthew-ngzc")
    print(separator)


def prompt_required(prompt_text: str) -> str:
    while True:
        value = input(ui_prompt(prompt_text)).strip()
        if value:
            return value
        print(ui_warning("This field is required. Please enter a value."))


def prompt_optional(prompt_text: str, default: str | None = None) -> str | None:
    value = input(ui_prompt(prompt_text)).strip()
    if not value:
        return default
    return value


def normalize_filename_template(user_value: str | None, default_template: str) -> str:
    if not user_value:
        return default_template

    value = user_value.strip()
    if "%(" in value:
        return value
    if value.endswith(".%(ext)s"):
        return value

    # If user enters a plain name, let yt-dlp choose the right file extension.
    return f"{value}.%(ext)s"


def resolve_cookie_file_path(cookie_file_value: str | None) -> Path | None:
    if not cookie_file_value:
        return None
    cookie_path = Path(cookie_file_value).expanduser()
    if cookie_path.is_absolute():
        return cookie_path
    script_dir = Path(__file__).resolve().parent
    return script_dir / "cookies" / cookie_path


def get_default_cookie_file_path() -> Path:
    script_dir = Path(__file__).resolve().parent
    return script_dir / "cookies" / "cookies.txt"


def looks_like_protected_recording_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    indicators = (
        "passcode",
        "password",
        "protected",
        "login",
        "authentication",
        "no video formats found",
        "unable to extract file id",
        "unable to extract data",
        "forbidden",
        "401",
        "403",
    )
    return any(indicator in msg for indicator in indicators)


def next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 1
    while True:
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def predict_output_path(
    url: str,
    output_dir: Path,
    filename_template: str,
    cookie_file_path: Path | None,
) -> Path | None:
    preflight_opts: dict[str, Any] = {
        "outtmpl": str(output_dir / filename_template),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if cookie_file_path:
        preflight_opts["cookiefile"] = str(cookie_file_path)
    try:
        with yt_dlp.YoutubeDL(cast(Any, preflight_opts)) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            return Path(ydl.prepare_filename(info))
    except Exception:
        return None


def resolve_outtmpl_with_collision_handling(
    url: str,
    output_dir: Path,
    filename_template: str,
    cookie_file_path: Path | None,
) -> str:
    default_outtmpl = str(output_dir / filename_template)
    predicted_path = predict_output_path(url, output_dir, filename_template, cookie_file_path)
    if predicted_path is None or not predicted_path.exists():
        return default_outtmpl

    print()
    print(ui_warning(f'File already exists: "{predicted_path.name}"'))
    new_name = prompt_optional(
        "Enter another filename (without extension), or press Enter for auto-numbering: ",
        default=None,
    )
    if new_name:
        proposed = Path(new_name)
        if proposed.suffix:
            candidate = output_dir / proposed.name
        else:
            candidate = output_dir / f"{proposed.name}{predicted_path.suffix}"
        if candidate.exists():
            candidate = next_available_path(candidate)
        print(ui_default(f'Using filename: "{candidate.name}"'))
        return str(candidate)

    auto_path = next_available_path(predicted_path)
    print(ui_default(f'Using filename: "{auto_path.name}"'))
    return str(auto_path)


def print_output_folder_help(cwd: Path, default_output_dir: str) -> None:
    print()
    print(ui_section("Choose where you want to download to"))
    print(ui_section("Output folder examples:"))
    print(
        ui_example(
            f'- Relative: if you enter "{default_output_dir}", it saves to '
            f'"{cwd / default_output_dir}" (relative to where you run the script).'
        )
    )
    print(ui_example('- Absolute: "D:\\Recordings\\Zoom"'))
    print(
        ui_default(
            f'- Default: press Enter at the output folder prompt to use "{default_output_dir}"'
            " in the current folder."
        )
    )


def print_cookies_help(cookies_dir: Path) -> None:
    print()
    print(ui_warning("Password-protected Zoom recordings: use cookies.txt only."))
    print(ui_warning("Passcode-only extraction is not supported in this script."))
    print(ui_section("Cookies file path examples:"))
    print(
        ui_example(
            '- Relative filename: if you enter "cookies.txt", it uses '
            f'"{cookies_dir / "cookies.txt"}".'
        )
    )
    print(
        ui_example(
            '- Relative path: if you enter "archive/cookies2.txt", it uses '
            f'"{cookies_dir / "archive" / "cookies2.txt"}".'
        )
    )
    print(ui_example('- Absolute: "D:\\Zoom\\cookies.txt"'))
    print(
        ui_default(
            "- Default: press Enter at the cookies prompt to skip cookies "
            "(works only for non-protected/public recordings)."
        )
    )


def print_download_start_separator() -> None:
    print()
    separator = gradient_text("=" * 118)
    print(separator)
    print(ui_section("Starting download..."))
    print(separator)


def collect_user_inputs() -> tuple[
    str,
    Path,
    str,
    Path | None,
]:
    cwd = Path.cwd()
    default_output_dir = "downloads"
    default_filename_template = "%(title)s.%(ext)s"
    print(ui_default("Enter values when prompted. If a field is not applicable, just press Enter."))

    url = prompt_required("Zoom recording URL: ")
    print_output_folder_help(cwd, default_output_dir)
    output_dir_value = prompt_optional(
        f"Output folder [e.g. {default_output_dir}]: ",
        default=default_output_dir,
    )
    print()
    filename_input = prompt_optional(
        "Filename (optional, extension not needed; press Enter for title-based default): ",
        default=default_filename_template,
    )
    script_dir = Path(__file__).resolve().parent
    cookies_dir = script_dir / "cookies"
    print_cookies_help(cookies_dir)
    cookie_file_value = prompt_optional(
        "Cookies file path [e.g. cookies.txt]: ",
        default=None,
    )

    return (
        url,
        Path(output_dir_value or default_output_dir),
        normalize_filename_template(filename_input, default_filename_template),
        resolve_cookie_file_path(cookie_file_value),
    )


def download_zoom_recording(
    url: str,
    output_dir: Path,
    filename_template: str,
    cookie_file_path: Path | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    def run_download(active_cookie_file_path: Path | None) -> None:
        progress_renderer = DownloadProgressRenderer()
        resolved_outtmpl = resolve_outtmpl_with_collision_handling(
            url,
            output_dir,
            filename_template,
            active_cookie_file_path,
        )
        ydl_opts = {
            "outtmpl": resolved_outtmpl,
            "noprogress": True,
            "continuedl": True,
            "retries": 10,
            "logger": YtDlpColorLogger(progress_renderer),
            "progress_hooks": [progress_renderer.hook],
        }
        if active_cookie_file_path:
            ydl_opts["cookiefile"] = str(active_cookie_file_path)
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            ydl.download([url])

    if cookie_file_path is not None:
        run_download(cookie_file_path)
        return

    try:
        run_download(None)
    except DownloadError as exc:
        default_cookie_file_path = get_default_cookie_file_path()
        if looks_like_protected_recording_error(exc) and default_cookie_file_path.exists():
            print()
            print(ui_warning("Detected protected recording. Retrying with default cookies file..."))
            print(ui_default(f'Using: "{default_cookie_file_path}"'))
            run_download(default_cookie_file_path)
            return
        raise


def main() -> None:
    configure_console_output()
    print_zoom_downloader_header()
    url, output_dir, filename_template, cookie_file_path = collect_user_inputs()
    print_download_start_separator()
    download_zoom_recording(
        url,
        output_dir,
        filename_template,
        cookie_file_path,
    )


if __name__ == "__main__":
    main()
