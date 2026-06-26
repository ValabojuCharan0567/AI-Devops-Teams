"""Incident management service."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from api.schemas import StatusEnum, EnvironmentEnum, SeverityEnum


class IncidentService:
    """Service for managing incidents in memory."""

    def __init__(self):
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def create(
        self,
        title: str,
        description: str,
        environment: EnvironmentEnum,
        severity: SeverityEnum,
        affected_service: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create and store a new incident."""
        incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        incident = {
            "id": incident_id,
            "title": title,
            "description": description,
            "environment": environment,
            "severity": severity,
            "affected_service": affected_service,
            "status": StatusEnum.PENDING,
            "created_at": now,
            "updated_at": now,
            "investigation_data": None,
            "report": None
        }

        self.incidents[incident_id] = incident
        return incident

    def get(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an incident by ID."""
        return self.incidents.get(incident_id)

    def list(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Return a paginated list of incidents."""
        incidents_list = list(self.incidents.values())
        return incidents_list[skip:skip + limit]

    def update(
        self,
        incident_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update allowed incident fields."""
        if incident_id not in self.incidents:
            return None

        incident = self.incidents[incident_id]
        incident["updated_at"] = datetime.now(timezone.utc)

        allowed_fields = {"status", "investigation_data", "report"}
        for key, value in kwargs.items():
            if key in allowed_fields:
                incident[key] = value

        return incident

    def count(self) -> int:
        """Return the number of incidents."""
        return len(self.incidents)


incident_service = IncidentService()
