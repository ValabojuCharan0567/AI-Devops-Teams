from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.metrics_tools import fetch_monitoring_activity


class MetricsAgent(BaseAgent):
    """Specialist agent for Grafana/Prometheus evidence."""

    name = "Metrics Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_monitoring_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "Monitoring evidence was collected from Prometheus and Grafana APIs. "
            "This helps identify service-level latency, error rates, and dashboard status."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "metrics", "monitoring_activity": activity}
        )
