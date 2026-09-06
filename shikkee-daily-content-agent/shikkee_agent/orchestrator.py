"""
Top-level daily run sequence. This file sequences the steps; it deliberately
does NOT contain the actual research/copywriting logic, since that step
("research today's news, write platform-native copy") is inherently a
judgment call best made by an LLM with live web search, not hardcoded rules.

Typical usage is `python scripts/run_daily.py`, which imports and calls
`run_daily_pipeline()` with today's already-written content passed in (see
scripts/run_daily.py for the wiring, and README.md for how this repo is meant
to be operated day to day: an LLM agent does the research + writing, then
calls into this package to validate, generate video, schedule, and log).
"""
from __future__ import annotations

from datetime import date
from shikkee_agent.pipeline import reconcile, blog_cross_post, reddit_track


def run_reconcile_and_cross_post() -> dict:
    """Step 0, every single run, before anything else."""
    reconcile_result = reconcile.reconcile()

    # Part A: only fires if a Blog record's WP post has actually flipped to
    # publish since it was last checked -- caller supplies candidate post IDs
    # (e.g. every Blog record's WordPress post id from the last N days).
    return {"reconcile": reconcile_result}


def run_reddit_if_scheduled_today(title: str, body: str) -> dict | None:
    subreddit = reddit_track.scheduled_subreddit_today()
    if not subreddit:
        return {"skipped": "not a scheduled Reddit day"}
    ok, message = reddit_track.draft_reddit_post(title, body)
    return {"ok": ok, "message": message}


def run_summary(today: date | None = None) -> str:
    today = today or date.today()
    return (
        f"Shikkee daily content agent run for {today.isoformat()}. "
        "See individual pipeline module return values / Airtable Content Pipeline "
        "table for the full per-channel breakdown."
    )
