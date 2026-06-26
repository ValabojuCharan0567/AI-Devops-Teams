from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from tools.llm_tools import generate_incident_review


class ReviewerAgent(BaseAgent):
    """Reviewer agent that validates evidence and assigns confidence."""

    name = "Reviewer Agent"

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        aggregate = incident.get("aggregate", {})
        evidence = aggregate.get("evidence", [])
        agent_summaries = aggregate.get("agent_summaries", [])

        review = generate_incident_review(incident.get("incident", {}), aggregate)

        details = {
            "confidence": review.get("confidence", 0.0),
            "root_cause": review.get("root_cause", "unknown"),
            "recommendation": review.get("recommendation", "Review the incident manually."),
            "reasoning": review.get("reasoning", ""),
            "agent_summaries": agent_summaries,
            "evidence_count": len(evidence)
        }

        return AgentResponse(
            agent_name=self.name,
            findings=review.get("findings", "Review completed."),
            evidence=evidence,
            details=details
        )
