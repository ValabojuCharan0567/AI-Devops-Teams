from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.aws_tools import fetch_aws_activity


class AWSAgent(BaseAgent):
    """Specialist agent for AWS incident evidence."""

    name = "AWS Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        activity = fetch_aws_activity(incident)
        evidence = activity.get("evidence", [])

        findings = (
            "AWS telemetry from CloudWatch, EC2, and RDS was collected. "
            "This gives infrastructure-level evidence during the incident window."
        )

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details={"source": "aws", "aws_activity": activity}
        )
