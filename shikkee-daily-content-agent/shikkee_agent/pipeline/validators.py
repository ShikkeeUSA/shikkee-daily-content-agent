"""
Mandatory pre-publish gates. Run validate_copy() on every piece of copy before
scheduling it on any channel -- this is the same-tier check as the brand
terminology / no-em-dash / tagging rules in the source spec, not optional polish.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from shikkee_agent.config.brand_rules import find_banned_terms, find_em_dashes


@dataclass
class ValidationResult:
    ok: bool
    banned_terms: list[str] = field(default_factory=list)
    em_dash_count: int = 0
    unverified_tags: list[str] = field(default_factory=list)

    def report(self) -> str:
        if self.ok:
            return "OK"
        lines = []
        if self.banned_terms:
            lines.append(f"Banned terms found: {', '.join(self.banned_terms)}")
        if self.em_dash_count:
            lines.append(f"{self.em_dash_count} em dash(es) found -- rewrite with period/comma/colon/semicolon/parens")
        if self.unverified_tags:
            lines.append(f"Unverified handles (named in plain text instead): {', '.join(self.unverified_tags)}")
        return "; ".join(lines)


def validate_copy(text: str, verified_tags: dict[str, str | None] | None = None) -> ValidationResult:
    """verified_tags: {"Entity Name": "@handle_or_None"}. Any entity mapped to
    None means no real handle could be confirmed -- that's fine (name them in
    plain text) but it's surfaced here so it ends up in the Airtable log."""
    banned = find_banned_terms(text)
    em_dashes = find_em_dashes(text)
    unverified = [name for name, handle in (verified_tags or {}).items() if handle is None]
    ok = not banned and em_dashes == 0
    return ValidationResult(ok=ok, banned_terms=banned, em_dash_count=em_dashes, unverified_tags=unverified)


def enforce_or_raise(text: str, context: str = "") -> None:
    result = validate_copy(text)
    if not result.ok:
        raise ValueError(f"Copy failed validation ({context}): {result.report()}\n---\n{text}")
