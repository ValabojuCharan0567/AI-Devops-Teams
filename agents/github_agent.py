from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.github_tools import fetch_github_activity


class GitHubAgent(BaseAgent):
    """Specialist agent that inspects GitHub activity for the incident."""

    name = "GitHub Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_github_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "GitHub activity was analyzed for commits, pull requests, and deployments. "
            "The findings capture recent repo health and release signals."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "github", "github_activity": activity}
        )
