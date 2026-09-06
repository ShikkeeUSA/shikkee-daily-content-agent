"""
Hard brand/legal constraints that apply to every piece of content, every channel,
every run. These are enforced programmatically in shikkee_agent/pipeline/validators.py
-- treat this file as the single source of truth for the rules themselves.
"""
import re

BANNED_TERMS = [
    "prefab",
    "prefabricated",
    "modular home",
    "modular construction",
    "modular",
]

EM_DASH = "—"  # "—"

CURRENT_CAMPAIGN_FACTS = {
    "offer": "First 100 Shikkee homes: 50% off.",
    "reservation": "$99 to reserve",
    "sweepstakes": "a chance to win one free home, no purchase necessary",
    # RESOLVED (2026-09-06): Tal confirmed directly, definitively, that Shikkee
    # ships Christmas 2026. This supersedes the earlier "September 2026" figure
    # and the prior unresolved September-vs-Christmas conflict noted here -- do
    # not use "September 2026" anymore.
    "ship_date": "Ships Christmas 2026",
    "cta_verb": "Shikkee it.",
}

BRAND_COLORS = {
    "pink": "#F11A7B",   # primary -- get this one exactly right, do not let a
                         # generator invent its own shade of pink
    "white": "#FFFFFF",
    "black": "#000000",
    "blush": "#F0DFE3",
}


def find_banned_terms(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in BANNED_TERMS if term in lowered]


def find_em_dashes(text: str) -> int:
    return text.count(EM_DASH)


def strip_em_dashes_hint(text: str) -> str:
    """Not an auto-fixer -- em dashes should be rewritten by hand (period, comma,
    colon, semicolon, or parentheses), whichever reads most naturally. This just
    flags where they are so a human or an LLM rewrite pass can fix them."""
    return "\n".join(
        f"[EM DASH at char {m.start()}] ...{text[max(0, m.start()-40):m.start()+40]}..."
        for m in re.finditer(EM_DASH, text)
    )
