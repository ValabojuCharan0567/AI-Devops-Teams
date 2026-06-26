from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.metrics_tools import fetch_network_activity


class NetworkAgent(BaseAgent):
    """Specialist agent that inspects network behavior."""

    name = "Network Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_network_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "Network telemetry was collected from Prometheus metrics and monitoring sources. "
            "This provides a more concrete view of packet, latency, and interface behavior."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "network", "network_activity": activity}
        )
