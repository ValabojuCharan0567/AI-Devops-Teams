from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.llm_tools import generate_incident_report


class ReportAgent(BaseAgent):
    """Agent that generates a consolidated report from specialist findings."""

    name = "Report Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        aggregate = incident.get("aggregate", {})
        evidence = aggregate.get("evidence", [])
        agent_summaries = aggregate.get("agent_summaries", [])
        review = incident.get("review", {})

        report = generate_incident_report(
            incident.get("incident", {}),
            aggregate,
            review
        )

        findings = report.get("summary", "Insufficient evidence available to reach a firm conclusion.")

        details = {
            "confidence_estimates": report.get("confidence_estimates", {}),
            "recommendation": report.get("recommendation", "Recommend human approval before rollback."),
            "reasoning": report.get("reasoning", ""),
            "agent_summaries": agent_summaries
        }

        return AgentResponse(
            agent_name=self.name,
            findings=findings,
            evidence=evidence,
            details=details
        )
