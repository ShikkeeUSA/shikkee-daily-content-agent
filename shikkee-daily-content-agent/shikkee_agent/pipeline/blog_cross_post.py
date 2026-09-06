"""
BLOG CROSS-POST & FOUNDER REPOST RULE. Two independent parts:

Part A -- SHIKKEE PROFILE: when a Blog WordPress post flips from draft to
published, auto-publish promo copy across 5 channels (LinkedIn/X/Facebook/GBP/
Instagram) with autoPublish=True. This is a DELIBERATE, EXPLICIT exception to
the draft-only rule everywhere else in this pipeline -- approved by Tal.

Part B -- FOUNDER PROFILES: rolling 2-day lookback. Both founders like+repost
any confirmed-live ShikkeeUSA LinkedIn/X post. The non-featured founder
like+reposts the featured founder's daily solo video post. This part requires
real browser sessions (see browser/playwright_session.py) since there is no
"like/repost as another account" API -- it drives the founder's own logged-in
browser.
"""
from __future__ import annotations

from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.clients.metricool_client import MetricoolClient
from shikkee_agent.clients.wordpress_client import WordPressClient
from shikkee_agent.config import settings

PART_A_NETWORKS = ("linkedin", "twitter", "facebook", "gmb")  # + instagram, handled separately (needs an image)


def find_newly_published_blog_posts(candidate_post_ids: list[int]) -> list[dict]:
    wp = WordPressClient()
    newly_published = []
    for post_id in candidate_post_ids:
        if wp.get_post_status(post_id) == "publish":
            if not _already_cross_posted(post_id):
                newly_published.append({"post_id": post_id})
    return newly_published


def _already_cross_posted(post_id: int) -> bool:
    airtable = AirtableClient()
    records = airtable.list_records(
        settings.airtable_content_table_id,
        formula=f"FIND('blog post {post_id}', {{Founder account}}) > 0",
    )
    return len(records) > 0


def cross_post_blog_to_five_channels(post_id: int, title: str, url: str, teaser: str, image_url: str | None) -> dict:
    """Part A. autoPublish=True is intentional here -- see module docstring."""
    metricool = MetricoolClient()
    results = {}
    for network in PART_A_NETWORKS:
        copy = f"{title}\n\n{teaser}\n\n{url}"
        payload = {
            "text": copy,
            "media": [image_url] if image_url else [],
            "providers": [{"network": network}],
        }
        results[network] = metricool.create_scheduled_post(
            settings.blog_shikkee_usa,
            _now_iso(),
            settings.timezone_shikkee_usa,
            {**payload, "draft": False},  # deliberate override of the draft-only default
        )
    if image_url:
        results["instagram"] = metricool.create_scheduled_post(
            settings.blog_shikkee_usa,
            _now_iso(),
            settings.timezone_shikkee_usa,
            {"text": teaser, "media": [image_url], "providers": [{"network": "instagram"}], "draft": False},
        )
    _log_part_a(post_id, results)
    return results


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%dT%H:%M:00")


def _log_part_a(post_id: int, results: dict) -> None:
    airtable = AirtableClient()
    today = _now_iso()[:10]
    records = [
        {
            "Publish date": today,
            "platform": network if network != "twitter" else "x",
            "Founder account": f"BLOG CROSS-POST (Part A) | source blog post {post_id}",
            "caption": "",
            "status": "posted",  # Part A auto-publishes -- status reflects that directly
            "submmited by": "Claude",
        }
        for network in results
    ]
    airtable.create_records(settings.airtable_content_table_id, records)
