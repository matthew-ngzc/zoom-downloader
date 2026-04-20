#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlparse

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
    sync_playwright,
)


def _first_visible(page: Page, selectors: list[str]) -> str | None:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible():
                return selector
        except Exception:
            continue
    return None


def _fill_passcode(page: Page, passcode: str) -> None:
    # Preferred path from codegen: role-based textbox named "Passcode".
    role_locator = page.get_by_role("textbox", name="Passcode")
    try:
        expect(role_locator.first).to_be_visible(timeout=10000)
        role_locator.first.fill(passcode)
        return
    except Exception:
        pass

    # Fallback CSS selectors for layout/label variants.
    passcode_selectors = [
        'input[type="password"]',
        'input[name*="pass" i]',
        'input[id*="pass" i]',
        'input[placeholder*="passcode" i]',
        'input[placeholder*="password" i]',
        'input[aria-label*="passcode" i]',
        'input[aria-label*="password" i]',
    ]
    passcode_selector = _first_visible(page, passcode_selectors)
    if not passcode_selector:
        raise RuntimeError(
            "E2E_DATA_ISSUE: Could not find passcode/password field on Zoom page."
        )
    page.fill(passcode_selector, passcode)


def _submit_passcode(page: Page) -> None:
    # Preferred path from codegen.
    watch_button = page.get_by_role("button", name="Watch Recording")
    try:
        if watch_button.first.is_visible(timeout=5000):
            watch_button.first.click()
            return
    except Exception:
        pass

    # Fallback buttons
    submit_selectors = [
        'button:has-text("Submit")',
        'button:has-text("View Recording")',
        'button:has-text("Continue")',
        'button[type="submit"]',
        'input[type="submit"]',
    ]
    submit_selector = _first_visible(page, submit_selectors)
    if submit_selector:
        page.locator(submit_selector).first.click()
    else:
        page.keyboard.press("Enter")


def _accept_cookie_banner_if_present(page: Page) -> None:
    # Common zoom button from codegen flow.
    candidates = [
        page.get_by_role("button", name="Accept Cookies"),
        page.get_by_role("button", name="Accept"),
        page.locator('button:has-text("Accept Cookies")'),
        page.locator('button:has-text("Accept")'),
    ]
    for locator in candidates:
        try:
            if locator.first.is_visible(timeout=2500):
                locator.first.click()
                return
        except Exception:
            continue


def _passcode_visible(page: Page) -> bool:
    passcode_selectors = [
        'input[type="password"]',
        'input[name*="pass" i]',
        'input[id*="pass" i]',
        'input[placeholder*="passcode" i]',
        'input[placeholder*="password" i]',
        'input[aria-label*="passcode" i]',
        'input[aria-label*="password" i]',
    ]
    return _first_visible(page, passcode_selectors) is not None


def _wait_for_unlock_state(page: Page, *, timeout_ms: int = 25000) -> bool:
    """Return True when passcode form disappears / recording page appears."""
    deadline = time.monotonic() + (timeout_ms / 1000)
    while time.monotonic() < deadline:
        if not _passcode_visible(page):
            return True
        # If URL has transitioned away from need-password page, consider it success.
        if "need-password" not in page.url:
            return True
        page.wait_for_timeout(400)
    return False


def _attempt_passcode_flow(page: Page, passcode: str, *, headless: bool) -> None:
    # Retry helps with flaky timing in fast/headless mode.
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        _fill_passcode(page, passcode)
        _submit_passcode(page)
        _accept_cookie_banner_if_present(page)

        # Headless mode tends to be timing-sensitive; keep deterministic delay.
        if headless:
            page.wait_for_timeout(900)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        if _wait_for_unlock_state(page, timeout_ms=12000):
            return

        if attempt < max_attempts:
            page.wait_for_timeout(1000)

    raise RuntimeError("E2E_DATA_ISSUE: Passcode was submitted but page still shows passcode input.")


def _write_netscape_cookie_file(
    cookie_file_path: Path, cookies: Sequence[Mapping[str, object]]
) -> None:
    lines = [
        "# Netscape HTTP Cookie File",
        "# This is a generated file! Do not edit.",
    ]
    for cookie in cookies:
        domain = cookie.get("domain", "")
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        path = cookie.get("path", "/")
        secure = "TRUE" if cookie.get("secure", False) else "FALSE"
        expires = cookie.get("expires", -1)
        expires_int = int(expires) if isinstance(expires, (int, float)) and expires > 0 else 0
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        lines.append(
            f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires_int}\t{name}\t{value}"
        )
    cookie_file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh_zoom_cookies(url: str, passcode: str, output_file: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://")
    if not passcode.strip():
        raise ValueError("Passcode is required")

    with sync_playwright() as p:
        headless = (os.getenv("E2E_PLAYWRIGHT_HEADED", "").strip().lower() not in {"1", "true", "yes", "on"})
        slow_mo_value = os.getenv("E2E_PLAYWRIGHT_SLOW_MO_MS", "").strip()
        slow_mo = int(slow_mo_value) if slow_mo_value.isdigit() else 0
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        _attempt_passcode_flow(page, passcode, headless=headless)

        cookies = context.cookies([f"{parsed.scheme}://{parsed.netloc}"])
        if not cookies:
            raise RuntimeError(
                "E2E_DATA_ISSUE: No cookies were captured from protected Zoom page."
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        _write_netscape_cookie_file(output_file, cookies)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Zoom cookies.txt by passcode flow")
    parser.add_argument("--url", required=True, help="Protected Zoom recording URL")
    parser.add_argument("--passcode", required=True, help="Recording passcode/password")
    parser.add_argument(
        "--output-file",
        default="cookies/refreshed_cookies.txt",
        help="Output Netscape cookies.txt path",
    )
    args = parser.parse_args()
    refresh_zoom_cookies(args.url, args.passcode, Path(args.output_file))


if __name__ == "__main__":
    main()
