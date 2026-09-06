#!/usr/bin/env python3
"""
Entry point for a daily run. This script is intentionally thin: it wires up
already-written content (from an LLM research + copywriting pass -- e.g. a
Claude session, or any other agent) into the pipeline modules that do the
mechanical work of validating, generating video, scheduling drafts, and
logging to Airtable.

Run it as: python scripts/run_daily.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shikkee_agent.orchestrator import run_reconcile_and_cross_post, run_summary
from shikkee_agent.pipeline import six_channel, founder_tracks, rotation


def main() -> None:
    print("=== Step 0: reconcile + blog cross-post/founder repost check ===")
    step0 = run_reconcile_and_cross_post()
    print(step0)

    # --- Everything below is a TEMPLATE. Replace the placeholder copy/scripts
    # with today's actual researched angle before running for real. This file
    # ships as a worked example, not a magic "figure out the news" button. ---

    print("\n=== Step: six-channel daily pipeline ===")
    print("(edit scripts/run_daily.py with today's copy, then uncomment below)")
    # copy = six_channel.ChannelCopy(...)
    # six_channel.schedule_six_channel(copy, video_script="...", real_asset_url="...", ...)

    print("\n=== Step: founder tracks (written-only, no avatar video -- discontinued 2026-09-06) ===")
    slay_founder, slay_method = rotation.today_featured_founder("FOUNDER SLAY")
    fen_founder, fen_method = rotation.today_featured_founder("FOUNDER EXPERT NUMBERS")
    print(f"Founder Slay featured: {slay_founder} (via {slay_method})")
    print(f"Founder Expert Numbers featured: {fen_founder} (via {fen_method})")
    # founder_tracks.run_founder_slay(post_copy="...", theme_letter="f", hook_summary="...", custom_image_url="...")
    # founder_tracks.run_founder_expert_numbers(post_copy="...", pool="A", stat_source="...", custom_image_url="...")

    print("\n" + run_summary())


if __name__ == "__main__":
    main()
