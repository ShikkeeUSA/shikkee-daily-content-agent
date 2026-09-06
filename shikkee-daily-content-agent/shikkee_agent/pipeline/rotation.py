"""
Founder rotation logic for the two independent daily video tracks (Founder Slay
and Founder Expert Numbers). Each track alternates Tal Levi / Ayala Chrysler
every calendar day, self-correcting off the most recent Airtable record for
that track rather than a naive fixed schedule (so a skipped day doesn't
permanently offset the rotation).
"""
from __future__ import annotations

from datetime import date, datetime
from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.config import settings

TAL = "Tal Levi"
AYALA = "Ayala Chrysler"

FOUNDER_SLAY_ANCHOR_DATE = date(2026, 8, 20)
FOUNDER_SLAY_ANCHOR_FOUNDER = TAL

FOUNDER_EXPERT_NUMBERS_ANCHOR_DATE = date(2026, 8, 4)
FOUNDER_EXPERT_NUMBERS_ANCHOR_FOUNDER = AYALA


def _other(founder: str) -> str:
    return AYALA if founder == TAL else TAL


def _most_recent_record(prefix: str) -> dict | None:
    airtable = AirtableClient()
    records = airtable.list_records(
        settings.airtable_content_table_id,
        formula=f"FIND('{prefix}', {{Founder account}}) > 0",
        sort=[{"field": "Publish date", "direction": "desc"}],
        max_records=5,
    )
    return records[0] if records else None


def _featured_founder_from_notes(notes: str) -> str | None:
    if TAL in notes and AYALA not in notes:
        return TAL
    if AYALA in notes and TAL not in notes:
        return AYALA
    # both or neither mentioned -- look for "Featured founder: X" explicitly
    import re

    m = re.search(r"Featured founder:\s*(Tal Levi|Ayala Chrysler)", notes)
    return m.group(1) if m else None


def today_featured_founder(track: str, today: date | None = None) -> tuple[str, str]:
    """track: 'FOUNDER SLAY' or 'FOUNDER EXPERT NUMBERS'.
    Returns (featured_founder, method) where method is 'airtable_lookup' or
    'anchor_fallback', so the caller can log which method decided rotation."""
    today = today or datetime.now().date()

    most_recent = _most_recent_record(track)
    if most_recent:
        notes = most_recent["fields"].get("Founder account", "")
        last_founder = _featured_founder_from_notes(notes)
        if last_founder:
            return _other(last_founder), "airtable_lookup"

    # Fallback to the fixed anchor, alternating strictly by calendar day.
    if track == "FOUNDER SLAY":
        anchor_date, anchor_founder = FOUNDER_SLAY_ANCHOR_DATE, FOUNDER_SLAY_ANCHOR_FOUNDER
    elif track == "FOUNDER EXPERT NUMBERS":
        anchor_date, anchor_founder = FOUNDER_EXPERT_NUMBERS_ANCHOR_DATE, FOUNDER_EXPERT_NUMBERS_ANCHOR_FOUNDER
    else:
        raise ValueError(f"Unknown track: {track}")

    days_since = (today - anchor_date).days
    featured = anchor_founder if days_since % 2 == 0 else _other(anchor_founder)
    return featured, "anchor_fallback"


def most_recent_theme(track: str = "FOUNDER SLAY") -> str | None:
    """Returns the recurring theme letter (a-f) used in the most recent
    FOUNDER SLAY record, so today's run picks a different one."""
    import re

    record = _most_recent_record(track)
    if not record:
        return None
    notes = record["fields"].get("Founder account", "")
    m = re.search(r"[Tt]heme \(([a-f])\)", notes)
    return m.group(1) if m else None
