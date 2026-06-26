from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.database_tools import fetch_database_activity


class DatabaseAgent(BaseAgent):
    """Specialist agent that inspects database behavior."""

    name = "Database Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_database_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "Database activity was collected from PostgreSQL statistics and connection state. "
            "This captures query and lock evidence relevant to the incident."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "database", "database_activity": activity}
        )
