from typing import Any, Dict, List

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config import settings


def fetch_slack_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    channel = settings.slack_channel
    if not settings.slack_token or not channel:
        return {
            "channel": channel,
            "message_count": 0,
            "evidence": ["Slack is not configured; skipping Slack channel analysis."],
            "messages": []
        }

    client = WebClient(token=settings.slack_token)
    evidence: List[str] = []
    messages: List[Dict[str, Any]] = []

    try:
        response = client.conversations_history(channel=channel, limit=20)
        messages = response.get("messages", [])
        evidence.append(f"Fetched {len(messages)} messages from Slack channel {channel}")

        timeline_mentions = [m for m in messages if any(k in (m.get("text", "").lower()) for k in ["incident", "deploy", "outage", "rollback"])]
        if timeline_mentions:
            evidence.append(f"Found {len(timeline_mentions)} incident-related Slack messages")
        else:
            evidence.append("No immediate incident-related keywords found in recent Slack messages.")

    except SlackApiError as err:
        evidence.append(f"Slack API error: {err.response.get('error', 'unknown')}")
    except Exception as exc:
        evidence.append(f"Slack connector error: {exc}")

    return {
        "channel": channel,
        "message_count": len(messages),
        "evidence": evidence,
        "messages": messages
    }
