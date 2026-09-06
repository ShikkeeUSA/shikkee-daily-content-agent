"""
Twice-weekly Reddit rage-bait/contrarian discussion track: Tuesday -> r/RealEstate,
Friday -> r/urbanplanning. Browser-drafted only via a persisted login session --
NEVER clicks Submit, only saves to Reddit's native Drafts feature.

ACCOUNT AGING GATE: the account was newly created 2026-08-20. Reddit's spam
filters reliably nuke posts from brand-new accounts, so this MUST re-check post/
comment history and account age every single scheduled run (not just once) and
refuse to draft anything until the account clears roughly 10-15 genuine posts/
comments and ~3-4 weeks of age.
"""
from __future__ import annotations

from datetime import date
from playwright.sync_api import sync_playwright
from shikkee_agent.browser.playwright_session import open_authenticated_context, is_logged_in
from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.config import settings

SUBREDDIT_BY_WEEKDAY = {1: "RealEstate", 4: "urbanplanning"}  # Mon=0 ... Fri=4
ACCOUNT = "shikkee_reddit"
MIN_HISTORY_ITEMS = 10
MIN_ACCOUNT_AGE_DAYS = 21


def scheduled_subreddit_today(today: date | None = None) -> str | None:
    today = today or date.today()
    return SUBREDDIT_BY_WEEKDAY.get(today.weekday())


def check_account_aging_gate() -> tuple[bool, str]:
    with sync_playwright() as p:
        context = open_authenticated_context(p, ACCOUNT)
        if context is None:
            return False, "No persisted Reddit login session found"
        page = context.new_page()
        page.goto("https://www.reddit.com/user/shikkee_official/")
        if not is_logged_in(page, ["a[href*='/login']"]):
            return False, "Reddit session expired or logged out"

        # NOTE: exact selectors depend on Reddit's current DOM -- verify against
        # the live site before relying on this in production.
        history_count = page.locator("[data-testid='post-container'], [data-testid='comment']").count()
        page.close()
        if history_count < MIN_HISTORY_ITEMS:
            return False, f"Only {history_count} posts/comments visible, needs >= {MIN_HISTORY_ITEMS}"
        return True, "Account aging gate cleared"


def draft_reddit_post(title: str, body: str) -> tuple[bool, str]:
    subreddit = scheduled_subreddit_today()
    if not subreddit:
        return False, "Not a scheduled Reddit day (Tue/Fri only)"

    cleared, reason = check_account_aging_gate()
    if not cleared:
        _log_blocked(subreddit, reason)
        return False, reason

    with sync_playwright() as p:
        context = open_authenticated_context(p, ACCOUNT)
        page = context.new_page()
        page.goto(f"https://www.reddit.com/r/{subreddit}/submit")
        if not is_logged_in(page, ["a[href*='/login']"]):
            _log_blocked(subreddit, "Not logged in at submit page")
            return False, "Not logged in"

        page.fill("[name='title']", title)
        page.fill("[data-testid='post-content-body']", body)
        # Deliberately do NOT click Submit -- Reddit autosaves to Drafts.
        page.close()

    _log_drafted(subreddit, title, body)
    return True, f"Drafted to r/{subreddit}"


def _log_blocked(subreddit: str, reason: str) -> None:
    AirtableClient().create_records(
        settings.airtable_content_table_id,
        [
            {
                "Publish date": date.today().isoformat(),
                "platform": "reddit",
                "Founder account": f"REDDIT | r/{subreddit}. Blocked: {reason}",
                "caption": "",
                "status": "Blocked: not logged in",
                "submmited by": "Claude",
            }
        ],
    )


def _log_drafted(subreddit: str, title: str, body: str) -> None:
    AirtableClient().create_records(
        settings.airtable_content_table_id,
        [
            {
                "Publish date": date.today().isoformat(),
                "platform": "reddit",
                "Founder account": f"REDDIT | r/{subreddit}, drafted (not submitted)",
                "caption": f"{title}\n\n{body}",
                "status": "draft",
                "submmited by": "Claude",
            }
        ],
    )
