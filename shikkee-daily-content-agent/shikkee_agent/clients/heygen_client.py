"""
HeyGen public API client (https://docs.heygen.com). Generates talking-avatar
videos for the founder-personal and company-spokesperson tracks.

Every call MUST:
  - pass an explicit avatar_id + voice_id (never rely on prompt text alone to
    pick the right persona -- HeyGen's generation can substitute avatars if the
    id is left implicit)
  - pass the brand kit id so logo + brand colors apply
  - attach 1-3 real Shikkee asset URLs so scenes are built around the real
    product instead of a generic/unbranded house
"""
from __future__ import annotations

import time
import requests
from shikkee_agent.config import settings

API_ROOT = "https://api.heygen.com"
REQUIRED_ASSET_SENTENCE = "use the attached assets in positive scenes as shikkee's brand and products"
NO_TEXT_OVER_FACE = (
    "If any on-screen text, caption, or graphic overlay is included, place it in a "
    "lower-third banner or top strip, never over the avatar's face or head."
)


class HeyGenClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.heygen_api_key
        if not self.api_key:
            raise RuntimeError("HEYGEN_API_KEY is not set")

    def _headers(self) -> dict:
        return {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

    def generate_avatar_video(
        self,
        script: str,
        avatar_id: str,
        voice_id: str,
        asset_urls: list[str],
        orientation: str = "portrait",
        brand_kit_id: str | None = None,
    ) -> str:
        """Returns a HeyGen video_id. Poll with get_video_status()."""
        dimension = {"width": 720, "height": 1280} if orientation == "portrait" else {"width": 1280, "height": 720}
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": {"type": "text", "input_text": script, "voice_id": voice_id},
                    "background": {
                        "type": "image",
                        "url": asset_urls[0] if asset_urls else None,
                    },
                }
            ],
            "dimension": dimension,
            "caption": True,
        }
        if brand_kit_id or settings.heygen_brand_kit_id:
            payload["brand_kit_id"] = brand_kit_id or settings.heygen_brand_kit_id

        resp = requests.post(f"{API_ROOT}/v2/video/generate", headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["data"]["video_id"]

    def get_video_status(self, video_id: str) -> dict:
        resp = requests.get(
            f"{API_ROOT}/v1/video_status.get",
            headers=self._headers(),
            params={"video_id": video_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["data"]

    def wait_for_completion(self, video_id: str, timeout_s: int = 600, poll_every_s: int = 15) -> dict:
        elapsed = 0
        while elapsed < timeout_s:
            status = self.get_video_status(video_id)
            if status["status"] in ("completed", "failed"):
                return status
            time.sleep(poll_every_s)
            elapsed += poll_every_s
        raise TimeoutError(f"HeyGen video {video_id} did not complete within {timeout_s}s")

    @staticmethod
    def build_prompt_footer(asset_note: str = "") -> str:
        """Appended to any prompt-style script so the two hard constraints
        (real-asset attachment + no-text-over-face) are always present."""
        parts = [NO_TEXT_OVER_FACE, REQUIRED_ASSET_SENTENCE]
        if asset_note:
            parts.append(asset_note)
        return " ".join(parts)
