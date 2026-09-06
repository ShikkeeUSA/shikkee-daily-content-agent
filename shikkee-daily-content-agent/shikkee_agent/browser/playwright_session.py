"""
Persisted-login browser sessions for platforms with no usable write API:
Reddit (drafts only, never submits), Medium (drafts only, never publishes),
and founder like+repost actions on LinkedIn/X.

This NEVER types a password. A human logs in once, interactively, via
save_login_session() (run manually, not as part of the scheduled pipeline),
which persists Playwright's storage_state (cookies + local storage) to
PLAYWRIGHT_STATE_DIR/<account>.json. Every subsequent automated run loads
that state and simply checks whether it's still logged in -- if not, the
action is skipped and logged as blocked, never re-attempted with credentials.
"""
from __future__ import annotations

import os
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext
from shikkee_agent.config import settings


def state_path(account: str) -> Path:
    d = Path(settings.playwright_state_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{account}.json"


def save_login_session(account: str, start_url: str) -> None:
    """Run this manually and interactively once per account:
        python -m shikkee_agent.browser.playwright_session --save tal_reddit https://reddit.com/login
    A real browser window opens, you log in by hand, then press Enter in the
    terminal to persist the session. No credentials ever touch this codebase.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(start_url)
        input(f"Log in to {account} in the opened browser window, then press Enter here to save the session...")
        context.storage_state(path=str(state_path(account)))
        browser.close()


def open_authenticated_context(playwright, account: str) -> BrowserContext | None:
    path = state_path(account)
    if not path.exists():
        return None
    browser = playwright.chromium.launch(headless=True)
    return browser.new_context(storage_state=str(path))


def is_logged_in(page, logged_out_selectors: list[str]) -> bool:
    """Pass a list of CSS selectors that only appear on a logged-out/login page
    (e.g. a 'Log in' button). If any are visible, treat the session as dead."""
    for selector in logged_out_selectors:
        if page.locator(selector).count() > 0:
            return False
    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4 and sys.argv[1] == "--save":
        save_login_session(account=sys.argv[2], start_url=sys.argv[3])
    else:
        print("Usage: python -m shikkee_agent.browser.playwright_session --save <account> <start_url>")
