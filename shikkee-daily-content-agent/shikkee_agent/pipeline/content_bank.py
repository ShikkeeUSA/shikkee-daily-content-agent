"""
CONTENT ANGLE BANK RULE: the RSS Feeds Airtable table is a bank/queue of
vetted-but-unused news angles, so the pipeline stops defaulting to a
mortgage-rate-tracker update every single day.
"""
from __future__ import annotations

from dataclasses import dataclass
from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.config import settings

STATUS_NEW = "New"
STATUS_REVIEWED = "Reviewed"
STATUS_SELECTED = "Selected"
STATUS_ARCHIVED = "Archived"


@dataclass
class Angle:
    record_id: str
    title: str
    source_name: str
    category: str
    published_date: str
    url: str
    shikkee_angle: str
    primary_quote: str
    relevance_score: float


def get_best_reviewed_angle() -> Angle | None:
    airtable = AirtableClient()
    records = airtable.list_records(
        settings.airtable_rss_table_id,
        formula=f"{{Status}} = '{STATUS_REVIEWED}'",
        sort=[{"field": "Relevance Score", "direction": "desc"}],
    )
    if not records:
        return None
    top = records[0]
    f = top["fields"]
    return Angle(
        record_id=top["id"],
        title=f.get("Title", ""),
        source_name=f.get("Source Name", ""),
        category=f.get("Category", ""),
        published_date=f.get("Published Date", ""),
        url=f.get("URL", ""),
        shikkee_angle=f.get("Shikkee Angle", ""),
        primary_quote=f.get("Primary Quote / Stat", ""),
        relevance_score=f.get("Relevance Score", 0),
    )


def archive_angle(record_id: str) -> None:
    AirtableClient().update_records(settings.airtable_rss_table_id, [{"id": record_id, "fields": {"Status": STATUS_ARCHIVED}}])


def bank_angle(
    title: str,
    source_name: str,
    category: str,
    published_date: str,
    url: str,
    shikkee_angle: str,
    primary_quote: str,
    why_it_matters: str,
    relevance_score: int,
    author: str = "",
    source_type: str = "News",
) -> dict:
    """Log a strong runner-up angle discovered during today's research so it
    isn't discarded -- future runs can pick it up via get_best_reviewed_angle()."""
    fields = {
        "Title": title,
        "Source Name": source_name,
        "Author": author,
        "Category": category,
        "Published Date": published_date,
        "URL": url,
        "Source Type": source_type,
        "Shikkee Angle": shikkee_angle,
        "Primary Quote / Stat": primary_quote,
        "Why It Matters": why_it_matters,
        "Relevance Score": relevance_score,
        "Status": STATUS_REVIEWED,
    }
    return AirtableClient().create_records(settings.airtable_rss_table_id, [fields])[0]


def recent_platform_used_mortgage_angle(platform_field_value: str, days: int = 2) -> bool:
    """Check whether either of the last N days' records for a platform (Blog or
    LinkedIn, typically) already used a mortgage-rate-tracker angle, so today's
    run knows not to reach for another one."""
    airtable = AirtableClient()
    records = airtable.list_records(
        settings.airtable_content_table_id,
        formula=f"AND({{platform}} = '{platform_field_value}', DATETIME_DIFF(TODAY(), {{Publish date}}, 'days') <= {days})",
    )
    return any("mortgage" in r["fields"].get("Founder account", "").lower() for r in records)
