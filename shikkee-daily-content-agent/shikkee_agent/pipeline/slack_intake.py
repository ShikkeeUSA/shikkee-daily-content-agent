"""
SLACK CONTENT INTAKE: standing daily track that watches #narrative for founder-
submitted content angles. Never drafts content until enough information exists
in the thread -- if a link can't be fetched and no screenshot/text was given,
that counts as insufficient, and the correct action is to ask in-thread and
stop, not guess.
"""
from __future__ import annotations

from shikkee_agent.clients.airtable_client import AirtableClient
from shikkee_agent.clients.slack_client import SlackClient
from shikkee_agent.config import settings

BOT_MESSAGE_MARKERS = ("Claude Tag", "legacy Claude in Slack bot", "Working in ")


def _is_bot_or_system_message(message: dict) -> bool:
    text = message.get("text", "")
    return message.get("subtype") in ("channel_join",) or any(marker in text for marker in BOT_MESSAGE_MARKERS)


def _has_claude_reply(thread_messages: list[dict], bot_user_id: str) -> bool:
    return any(m.get("user") == bot_user_id for m in thread_messages[1:])


def check_narrative_channel(bot_user_id: str, since_ts: str | None = None) -> list[dict]:
    """Returns a list of {"message": ..., "action": "ask" | "draft", "reason": str}
    for every qualifying thread. Caller decides what to actually draft based on
    the idea's content -- this function only does the triage."""
    slack = SlackClient()
    messages = slack.read_channel(oldest=since_ts)
    outcomes = []

    for message in messages:
        if _is_bot_or_system_message(message):
            continue
        if not message.get("thread_ts") and not message.get("reply_count"):
            # No thread yet -- treat the parent itself as the thing to triage
            thread = [message]
        else:
            thread = slack.read_thread(settings.slack_narrative_channel_id, message["ts"])

        if _has_claude_reply(thread, bot_user_id):
            # Check whether a human replied *after* Claude's last reply with new info
            last_claude_idx = max(i for i, m in enumerate(thread) if m.get("user") == bot_user_id)
            if last_claude_idx == len(thread) - 1:
                continue  # still pending, nothing new -- skip silently, don't re-ask
            new_reply = thread[last_claude_idx + 1]
            outcomes.append({"message": message, "new_info": new_reply, "action": "evaluate"})
        else:
            outcomes.append({"message": message, "action": "evaluate"})

    return outcomes


def has_enough_information(message_text: str, has_link: bool, link_fetchable: bool, has_screenshot: bool) -> bool:
    if not has_link and not has_screenshot:
        return bool(message_text.strip())  # a plain-text idea with no external source is fine
    if has_link and not link_fetchable and not has_screenshot:
        return False  # exactly the case the source spec calls out: never fabricate from an unfetchable link
    return True


def ask_for_missing_info(thread_ts: str, missing: str) -> None:
    SlackClient().reply_in_thread(
        settings.slack_narrative_channel_id,
        thread_ts,
        f"I need one more thing before I can draft this: {missing}",
    )


def confirm_drafted(thread_ts: str, where: str) -> None:
    SlackClient().reply_in_thread(settings.slack_narrative_channel_id, thread_ts, f"Drafted: {where}, ready for review.")


def log_slack_idea(platform: str, notes: str, caption: str) -> None:
    from datetime import date

    AirtableClient().create_records(
        settings.airtable_content_table_id,
        [
            {
                "Publish date": date.today().isoformat(),
                "platform": platform,
                "Founder account": f"SLACK IDEA | {notes}",
                "caption": caption,
                "status": "draft",
                "submmited by": "Claude",
            }
        ],
    )
