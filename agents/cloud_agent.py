from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.aws_tools import fetch_aws_activity
from tools.metrics_tools import fetch_monitoring_activity


class CloudAgent(BaseAgent):
    """Specialist agent that inspects cloud infrastructure metrics."""

    name = "Cloud Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        aws_activity = fetch_aws_activity(incident)
        monitoring_activity = fetch_monitoring_activity(incident)

        evidence = aws_activity.get("evidence", []) + monitoring_activity.get("evidence", [])

        problems = [
            line for line in evidence
            if any(keyword in line.lower() for keyword in ["alarm", "non-running", "failed", "error", "critical", "not configured"])
        ]

        if problems:
            findings = (
                "Cloud investigation identified potential issues from AWS and monitoring telemetry: "
                + " ; ".join(problems[:3])
            )
        else:
            findings = (
                "Cloud investigation completed. No critical cloud alerts were detected in the available AWS and monitoring telemetry."
            )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={
                "source": "cloud",
                "aws_activity": aws_activity,
                "monitoring_activity": monitoring_activity
            }
        )
