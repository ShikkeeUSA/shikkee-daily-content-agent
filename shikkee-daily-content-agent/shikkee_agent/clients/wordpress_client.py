"""
WordPress REST API client for shikkee.com (Cloudways-hosted, RankMath SEO plugin).

Auth: HTTP Basic Auth using a WordPress Application Password (WP-Admin -> Users ->
[user] -> Application Passwords). Never commit the real password -- it comes from
WORDPRESS_APP_PASSWORD in the environment.

Known operational gotcha (2026-09-04): the site sits behind Cloudways / Cloudflare /
Wordfence (or Imunify360, depending on the day). Some non-standard endpoints --
notably /wp-json/rankmath/v1/updateMeta -- can get flagged and blocked with a bare
403 "potentially unsafe operation detected" even with valid credentials. That is a
hosting-level bot-protection block on the calling IP, not a payload bug. If it
happens, don't retry indefinitely: surface it as a blocker (the WordPress draft
itself still counts as done) and ask the site owner to allowlist the automation
IP / endpoint.
"""
from __future__ import annotations

import requests
from requests.auth import HTTPBasicAuth
from shikkee_agent.config import settings

WP_API = "wp-json/wp/v2"
RANKMATH_API = "wp-json/rankmath/v1"


class WordPressClient:
    def __init__(self, base_url: str | None = None, username: str | None = None, app_password: str | None = None):
        self.base_url = (base_url or settings.wp_base_url).rstrip("/")
        self.auth = HTTPBasicAuth(username or settings.wp_username, app_password or settings.wp_app_password)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path}"

    def create_draft_post(
        self,
        title: str,
        content_html: str,
        slug: str,
        excerpt: str,
        category_ids: list[int],
        tag_ids: list[int],
    ) -> dict:
        payload = {
            "title": title,
            "slug": slug,
            "content": content_html,
            "excerpt": excerpt,
            "status": "draft",  # never "publish" -- draft only, human approves in WP-Admin
            "categories": category_ids,
            "tags": tag_ids,
        }
        resp = requests.post(self._url(f"{WP_API}/posts"), auth=self.auth, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def set_featured_media(self, post_id: int, media_id: int) -> dict:
        resp = requests.post(
            self._url(f"{WP_API}/posts/{post_id}"),
            auth=self.auth,
            json={"featured_media": media_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def upload_media(self, file_path: str, filename: str, content_type: str = "image/png") -> dict:
        with open(file_path, "rb") as f:
            resp = requests.post(
                self._url(f"{WP_API}/media"),
                auth=self.auth,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": content_type,
                },
                data=f.read(),
                timeout=60,
            )
        resp.raise_for_status()
        return resp.json()

    def set_media_alt_text(self, media_id: int, alt_text: str) -> dict:
        resp = requests.post(
            self._url(f"{WP_API}/media/{media_id}"),
            auth=self.auth,
            json={"alt_text": alt_text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_categories(self) -> list[dict]:
        resp = requests.get(self._url(f"{WP_API}/categories"), auth=self.auth, params={"per_page": 100}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_tags(self) -> list[dict]:
        resp = requests.get(self._url(f"{WP_API}/tags"), auth=self.auth, params={"per_page": 100}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def search_media(self, query: str) -> list[dict]:
        resp = requests.get(
            self._url(f"{WP_API}/media"), auth=self.auth, params={"search": query, "per_page": 40}, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def push_rankmath_meta(
        self,
        post_id: int,
        title: str,
        description: str,
        focus_keyword: str,
        rich_snippet: str = "article",
    ) -> tuple[bool, str]:
        """Returns (success, message). Does not raise on the known Wordfence/Imunify
        block -- treat a False return as a partial blocker, not a fatal error for
        the whole Blog channel."""
        try:
            resp = requests.post(
                self._url(f"{RANKMATH_API}/updateMeta"),
                auth=self.auth,
                json={
                    "objectType": "post",
                    "objectID": post_id,
                    "meta": {
                        "rank_math_title": title,
                        "rank_math_description": description,
                        "rank_math_focus_keyword": focus_keyword,
                        "rank_math_rich_snippet": rich_snippet,
                    },
                },
                timeout=30,
            )
            if resp.status_code == 200:
                return True, "ok"
            return False, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.RequestException as exc:
            return False, str(exc)

    def get_post_status(self, post_id: int) -> str:
        resp = requests.get(self._url(f"{WP_API}/posts/{post_id}"), params={"_fields": "status"}, timeout=30)
        resp.raise_for_status()
        return resp.json()["status"]
