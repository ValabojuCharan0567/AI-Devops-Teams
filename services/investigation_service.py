from typing import Any, Dict

from agents.base_agent import AgentResponse
from agents.manager_agent import ManagerAgent


class InvestigationService:
    """Orchestrates incident investigation via the LangGraph manager."""

    def __init__(self):
        self.manager = ManagerAgent()

    async def run_agents(self, incident: Dict[str, Any]) -> AgentResponse:
        """Run an incident investigation through the manager workflow."""
        return await self.manager.execute(incident)


investigation_service = InvestigationService()
