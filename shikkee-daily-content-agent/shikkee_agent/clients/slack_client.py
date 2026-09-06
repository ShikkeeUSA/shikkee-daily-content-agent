"""Thin wrapper over slack_sdk for the #narrative content-intake track."""
from __future__ import annotations

from slack_sdk import WebClient
from shikkee_agent.config import settings


class SlackClient:
    def __init__(self, token: str | None = None):
        self.client = WebClient(token=token or settings.slack_bot_token)

    def read_channel(self, channel_id: str | None = None, oldest: str | None = None, limit: int = 100) -> list[dict]:
        resp = self.client.conversations_history(
            channel=channel_id or settings.slack_narrative_channel_id, oldest=oldest, limit=limit
        )
        return resp["messages"]

    def read_thread(self, channel_id: str, message_ts: str) -> list[dict]:
        resp = self.client.conversations_replies(channel=channel_id, ts=message_ts)
        return resp["messages"]

    def reply_in_thread(self, channel_id: str, thread_ts: str, text: str) -> dict:
        return self.client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, text=text)
