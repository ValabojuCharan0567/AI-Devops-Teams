from typing import Any, Dict

from .base_agent import AgentResponse, BaseAgent
from graphs.investigation_workflow import create_investigation_workflow


class ManagerAgent(BaseAgent):
    """LangGraph manager orchestrator agent."""

    name = "Manager Agent"

    def __init__(self):
        self.workflow = create_investigation_workflow()

    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        """Execute the LangGraph workflow for a given incident."""
        initial_state = {
            "incident": incident,
            "agent_results": [],
            "aggregate": {},
            "review": {},
            "report": {},
            "status": "pending"
        }

        output = await self.workflow.ainvoke(initial_state)
        report = output.get("report", {})
        return AgentResponse(
            agent_name=self.name,
            findings="Managed investigation workflow completed.",
            evidence=report.get("evidence", []),
            details={
                "status": output.get("status", "unknown"),
                "review": output.get("review", {}),
                "report": report,
                "aggregate": output.get("aggregate", {}),
                "agent_results": output.get("agent_results", [])
            }
        )
