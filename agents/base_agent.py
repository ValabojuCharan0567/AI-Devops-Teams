from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentResponse:
    """Standard response structure returned by each agent."""
    agent_name: str
    findings: str
    evidence: List[str] = field(default_factory=list)
    status: str = "completed"
    details: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for every specialist or review agent."""

    name: str = "BaseAgent"

    @abstractmethod
    async def execute(self, incident: Dict[str, Any]) -> AgentResponse:
        """Run the agent against an incident and return structured results."""
        raise NotImplementedError
