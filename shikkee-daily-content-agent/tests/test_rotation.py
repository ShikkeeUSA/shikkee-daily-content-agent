from datetime import date
from unittest.mock import patch
from shikkee_agent.pipeline.rotation import today_featured_founder, TAL, AYALA


def test_anchor_fallback_alternates_by_day():
    with patch("shikkee_agent.pipeline.rotation._most_recent_record", return_value=None):
        founder_day0, method0 = today_featured_founder("FOUNDER SLAY", today=date(2026, 8, 20))
        founder_day1, method1 = today_featured_founder("FOUNDER SLAY", today=date(2026, 8, 21))
        founder_day2, method2 = today_featured_founder("FOUNDER SLAY", today=date(2026, 8, 22))

    assert founder_day0 == TAL
    assert founder_day1 == AYALA
    assert founder_day2 == TAL
    assert method0 == method1 == method2 == "anchor_fallback"


def test_airtable_lookup_takes_priority_and_self_corrects():
    fake_record = {"fields": {"Founder account": "FOUNDER SLAY | Featured founder: Ayala Chrysler theme (c)"}}
    with patch("shikkee_agent.pipeline.rotation._most_recent_record", return_value=fake_record):
        founder, method = today_featured_founder("FOUNDER SLAY", today=date(2026, 9, 4))
    assert founder == TAL  # the OTHER founder from whoever ran last
    assert method == "airtable_lookup"
