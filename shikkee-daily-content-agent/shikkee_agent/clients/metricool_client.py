"""
Wrapper over Metricool's public API (https://developers.metricool.com).
Auth is via the X-Mc-Auth header (account API token) plus userId/blogId query
params. Double-check exact param names against current Metricool docs before
relying on this in production -- their scheduler endpoint shape has changed
over time and this client mirrors the most recent documented contract known
at the time this repo was written.

Every post this pipeline creates MUST be draft=True / autoPublish=False.
Metricool's draft state (or WordPress's draft status, for Blog) is the human
approval checkpoint -- never flip either of those to publish/schedule directly,
except the one deliberate, explicit exception in blog_cross_post.py Part A.
"""
from __future__ import annotations

import requests
from shikkee_agent.config import settings

API_ROOT = "https://app.metricool.com/api"


class MetricoolClient:
    def __init__(self, user_token: str | None = None, user_id: str | None = None):
        self.user_token = user_token or settings.metricool_user_token
        self.user_id = user_id or settings.metricool_user_id
        if not self.user_token:
            raise RuntimeError("METRICOOL_USER_TOKEN is not set")

    def _headers(self) -> dict:
        return {"X-Mc-Auth": self.user_token, "Content-Type": "application/json"}

    def get_scheduled_posts(self, blog_id: str, from_date: str, to_date: str) -> list[dict]:
        params = {"userId": self.user_id, "blogId": blog_id, "start": from_date, "end": to_date}
        resp = requests.get(f"{API_ROOT}/v2/scheduler/posts", headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def create_scheduled_post(self, blog_id: str, publication_date_iso: str, timezone: str, payload: dict) -> dict:
        """payload should already be in draft=True / autoPublish=False shape --
        see pipeline modules for the exact per-channel payload construction."""
        payload = {**payload, "draft": True, "autoPublish": False}
        body = {
            "providers": payload.pop("providers"),
            "publicationDate": {"dateTime": publication_date_iso, "timezone": timezone},
            **payload,
        }
        params = {"userId": self.user_id, "blogId": blog_id}
        resp = requests.post(
            f"{API_ROOT}/v2/scheduler/posts",
            headers=self._headers(),
            params=params,
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_brand_settings(self) -> list[dict]:
        resp = requests.get(
            f"{API_ROOT}/admin/simpleProfiles",
            headers=self._headers(),
            params={"userId": self.user_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
