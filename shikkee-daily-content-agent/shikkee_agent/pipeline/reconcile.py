"""
RECONCILE-FIRST RULE: runs before any new content generation, every single run.

Scans Metricool's scheduled posts across ShikkeeUSA + both founder brands (and
WordPress for any Blog record still "draft" in Airtable) covering at minimum
yesterday, ideally the last few days. Any Airtable "draft" record whose
corresponding post is now actually live gets flipped to "posted". Any live
Metricool post with no matching Airtable record gets backfilled (this can
happen because a separate legacy Make.com automation also publishes to the
same accounts directly, bypassing Airtable).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.clients.metricool_client import MetricoolClient
from shikkee_agent.clients.wordpress_client import WordPressClient
from shikkee_agent.config import settings

STATUS_DRAFT = "draft"
STATUS_POSTED = "posted"


def reconcile(lookback_days: int = 3) -> dict:
    airtable = AirtableClient()
    metricool = MetricoolClient()
    wp = WordPressClient()

    now = datetime.utcnow()
    from_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%dT00:00:00")
    to_date = now.strftime("%Y-%m-%dT23:59:59")

    blogs = {
        "ShikkeeUSA": settings.blog_shikkee_usa,
        "Tal Personal": settings.blog_tal_personal,
        "Ayala Profile": settings.blog_ayala_profile,
    }

    live_posts_by_brand: dict[str, list[dict]] = {}
    for label, blog_id in blogs.items():
        try:
            live_posts_by_brand[label] = metricool.get_scheduled_posts(blog_id, from_date, to_date)
        except Exception as exc:  # noqa: BLE001 -- surface, don't crash the whole run
            live_posts_by_brand[label] = []
            print(f"[reconcile] WARN: could not fetch posts for {label}: {exc}")

    draft_records = airtable.list_records(
        settings.airtable_content_table_id,
        formula="{status} = 'draft'",
    )

    updates = []
    for record in draft_records:
        fields = record.get("fields", {})
        notes = fields.get("Founder account", "")
        matched_post = _find_matching_post(notes, live_posts_by_brand)
        if matched_post and _is_published(matched_post):
            updates.append({"id": record["id"], "fields": {"status": STATUS_POSTED}})

    if updates:
        airtable.update_records(settings.airtable_content_table_id, updates)

    # Blog reconciliation: any Airtable "draft" Blog record whose WP post has
    # actually flipped to publish gets marked posted too.
    blog_drafts = [r for r in draft_records if r.get("fields", {}).get("platform") == "blog"]
    for record in blog_drafts:
        notes = record.get("fields", {}).get("Founder account", "")
        post_id = _extract_wp_post_id(notes)
        if post_id and wp.get_post_status(post_id) == "publish":
            airtable.update_records(
                settings.airtable_content_table_id, [{"id": record["id"], "fields": {"status": STATUS_POSTED}}]
            )

    return {
        "checked_records": len(draft_records),
        "updated_to_posted": len(updates),
        "live_posts_scanned": {k: len(v) for k, v in live_posts_by_brand.items()},
    }


def _is_published(post: dict) -> bool:
    return any(p.get("status") == "PUBLISHED" for p in post.get("providers", []))


def _find_matching_post(notes: str, live_posts_by_brand: dict[str, list[dict]]) -> dict | None:
    """Notes fields typically embed 'Metricool post id 123456789' -- match on that
    when present, since it's the most reliable link back to the live post."""
    import re

    m = re.search(r"[Mm]etricool post id[:\s]+(\d+)", notes)
    if not m:
        return None
    target_id = int(m.group(1))
    for posts in live_posts_by_brand.values():
        for post in posts:
            if post.get("id") == target_id:
                return post
    return None


def _extract_wp_post_id(notes: str) -> int | None:
    import re

    m = re.search(r"WordPress post id[:\s]+(\d+)", notes)
    return int(m.group(1)) if m else None
