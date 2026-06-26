from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.slack_tools import fetch_slack_activity


class SlackAgent(BaseAgent):
    """Specialist agent for Slack incident discussion evidence."""

    name = "Slack Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_slack_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "Slack channel activity was reviewed for incident-related messages, "
            "providing collaboration and timeline evidence for the outage."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "slack", "slack_activity": activity}
        )
