"""
Founder Slay (brand-attitude, daily) and Founder Expert Numbers (numbers-driven,
daily) written tracks. Both run their own independent Tal/Ayala rotation (see
rotation.py) and post only to that founder's own personal Metricool brand.

FOUNDER AVATAR VIDEO DISCONTINUED (2026-09-06, per Tal's explicit instruction):
neither track generates a HeyGen avatar video anymore. Both tracks post ONLY to
LinkedIn and X, and per the LINKEDIN & X MEDIA RULE those posts never carried
the video anyway -- so there is no reason left to generate one. Each post is
plain copy, optionally with a custom static picture (pass via
`custom_image_url`), or no image at all. Do not reintroduce a HeyGenClient call
here without a fresh, explicit instruction from Tal.
"""
from __future__ import annotations

from datetime import datetime
from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.clients.metricool_client import MetricoolClient
from shikkee_agent.config import settings
from shikkee_agent.pipeline.rotation import today_featured_founder
from shikkee_agent.pipeline.validators import enforce_or_raise

RECURRING_THEMES = {
    "a": "AI hype and wrappers -- Shikkee is hardware + OS, not a thin AI wrapper.",
    "b": "Female founders get ~1.7% of VC capital. Shikkee doesn't wait for that to become fair.",
    "c": "Bringing back the American Dream -- housing affordable again.",
    "d": "Founder-market fit -- Tal's architecture/IDF background, Ayala's track record.",
    "e": "Silicon Valley mockery -- valuations/headcount/hype vs. real problems.",
    "f": "Go-to-market independence -- already selling, don't need permission from big checks.",
}

_BLOG_ID_BY_FOUNDER = {
    "Tal Levi": lambda: settings.blog_tal_personal,
    "Ayala Chrysler": lambda: settings.blog_ayala_profile,
}


def _persona_blog_id(founder_name: str) -> str:
    return _BLOG_ID_BY_FOUNDER[founder_name]()


def _media_dict(custom_image_url: str | None) -> dict:
    """LINKEDIN & X MEDIA RULE: custom picture or no image -- never a video."""
    return {"media": [custom_image_url]} if custom_image_url else {}


def run_founder_slay(
    post_copy: str,
    theme_letter: str,
    hook_summary: str,
    custom_image_url: str | None = None,
) -> dict:
    """post_copy: the finished LinkedIn/X copy (no avatar video is generated
    for this track -- see FOUNDER AVATAR VIDEO DISCONTINUED above)."""
    founder, method = today_featured_founder("FOUNDER SLAY")
    enforce_or_raise(post_copy, context="founder_slay")

    metricool = MetricoolClient()
    blog_id = _persona_blog_id(founder)
    today = datetime.now().strftime("%Y-%m-%d")
    media = _media_dict(custom_image_url)

    li = metricool.create_scheduled_post(
        blog_id, f"{today}T16:00:00", settings.timezone_founders,
        {"text": post_copy, **media, "providers": [{"network": "linkedin"}], "linkedinData": {"type": "post"}},
    )
    x = metricool.create_scheduled_post(
        blog_id, f"{today}T16:10:00", settings.timezone_founders,
        {"text": post_copy, **media, "providers": [{"network": "twitter"}]},
    )

    notes = (
        f"FOUNDER SLAY | Featured founder: {founder} (rotation method: {method}). "
        f"Theme ({theme_letter}): {RECURRING_THEMES[theme_letter]}. Hook: {hook_summary}. "
        f"Media: {'custom picture' if custom_image_url else 'text-only (no image)'} per LINKEDIN & X MEDIA RULE. "
        f"No avatar video generated for this track (discontinued 2026-09-06)."
    )
    AirtableClient().create_records(
        settings.airtable_content_table_id,
        [
            {"Publish date": today, "platform": "linkedin", "Founder account": notes, "caption": post_copy, "status": "draft", "submmited by": "Claude"},
            {"Publish date": today, "platform": "x", "Founder account": notes, "caption": post_copy, "status": "draft", "submmited by": "Claude"},
        ],
    )
    return {"founder": founder, "method": method, "linkedin": li, "x": x}


def run_founder_expert_numbers(
    post_copy: str,
    pool: str,
    stat_source: str,
    custom_image_url: str | None = None,
) -> dict:
    """pool: 'A' (Silicon Valley/tech) or 'B' (real-world-cost). post_copy: the
    finished LinkedIn/X copy (no avatar video is generated for this track --
    see FOUNDER AVATAR VIDEO DISCONTINUED above)."""
    founder, method = today_featured_founder("FOUNDER EXPERT NUMBERS")
    enforce_or_raise(post_copy, context="founder_expert_numbers")

    metricool = MetricoolClient()
    blog_id = _persona_blog_id(founder)
    today = datetime.now().strftime("%Y-%m-%d")
    media = _media_dict(custom_image_url)

    li = metricool.create_scheduled_post(
        blog_id, f"{today}T16:00:00", settings.timezone_founders,
        {"text": post_copy, **media, "providers": [{"network": "linkedin"}], "linkedinData": {"type": "post"}},
    )
    x = metricool.create_scheduled_post(
        blog_id, f"{today}T16:10:00", settings.timezone_founders,
        {"text": post_copy, **media, "providers": [{"network": "twitter"}]},
    )

    notes = (
        f"FOUNDER EXPERT NUMBERS | Featured founder: {founder} (rotation method: {method}). Pool {pool}, source: {stat_source}. "
        f"Media: {'custom picture' if custom_image_url else 'text-only (no image)'} per LINKEDIN & X MEDIA RULE. "
        f"No avatar video generated for this track (discontinued 2026-09-06)."
    )
    AirtableClient().create_records(
        settings.airtable_content_table_id,
        [
            {"Publish date": today, "platform": "linkedin", "Founder account": notes, "caption": post_copy, "status": "draft", "submmited by": "Claude"},
            {"Publish date": today, "platform": "x", "Founder account": notes, "caption": post_copy, "status": "draft", "submmited by": "Claude"},
        ],
    )
    return {"founder": founder, "method": method, "linkedin": li, "x": x}
