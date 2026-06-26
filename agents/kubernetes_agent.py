from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.kubernetes_tools import fetch_kubernetes_activity


class KubernetesAgent(BaseAgent):
    """Specialist agent that inspects Kubernetes cluster signals."""

    name = "Kubernetes Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_kubernetes_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "Kubernetes cluster activity was evaluated from pod status, events, "
            "and recent logs. This provides direct container-level evidence for the incident."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "kubernetes", "kubernetes_activity": activity}
        )
