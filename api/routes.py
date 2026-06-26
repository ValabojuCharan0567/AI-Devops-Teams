"""API routes"""

from fastapi import APIRouter, HTTPException, status
from typing import List
import uuid
from datetime import datetime, timezone

from api.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentDetailResponse,
    ApprovalRequest,
    ApprovalResponse,
    StatusEnum,
    HealthCheck
)
from app import __version__
from app.config import settings
from services.incident_service import incident_service
from services.investigation_service import investigation_service


router = APIRouter(prefix="/api", tags=["incidents"])


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        version=__version__,
        environment=settings.env
    )


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new incident",
    description="Create a new incident for investigation"
)
async def create_incident(incident: IncidentCreate) -> IncidentResponse:
    """Create a new incident record."""
    incident_data = incident_service.create(
        title=incident.title,
        description=incident.description,
        environment=incident.environment,
        severity=incident.severity,
        affected_service=incident.affected_service
    )

    manager_response = await investigation_service.run_agents(incident_data)
    report = manager_response.details.get("report", {})
    incident_status = StatusEnum.RESOLVED if report else StatusEnum.FAILED

    updated_incident = incident_service.update(
        incident_data["id"],
        status=incident_status,
        investigation_data={
            "manager": {
                "findings": manager_response.findings,
                "status": manager_response.details.get("status", "unknown"),
                "review": manager_response.details.get("review", {}),
                "aggregate": manager_response.details.get("aggregate", {}),
                "agent_results": manager_response.details.get("agent_results", [])
            }
        },
        report=report
    )

    if updated_incident is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist incident data"
        )

    return IncidentResponse(
        id=updated_incident["id"],
        title=updated_incident["title"],
        environment=updated_incident["environment"],
        severity=updated_incident["severity"],
        status=updated_incident["status"],
        created_at=updated_incident["created_at"]
    )


@router.get(
    "/incidents",
    response_model=List[IncidentResponse],
    summary="List all incidents",
    description="Get paginated list of incidents"
)
async def list_incidents(skip: int = 0, limit: int = 10) -> List[IncidentResponse]:
    """List incidents with pagination."""
    if limit > 100:
        limit = 100

    incidents_list = incident_service.list(skip=skip, limit=limit)

    return [
        IncidentResponse(
            id=inc["id"],
            title=inc["title"],
            environment=inc["environment"],
            severity=inc["severity"],
            status=inc["status"],
            created_at=inc["created_at"]
        )
        for inc in incidents_list
    ]


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentDetailResponse,
    summary="Get incident details",
    description="Get detailed information about a specific incident"
)
async def get_incident(incident_id: str) -> IncidentDetailResponse:
    """Get detailed incident information by ID."""
    incident = incident_service.get(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )

    return IncidentDetailResponse(
        id=incident["id"],
        title=incident["title"],
        description=incident["description"],
        environment=incident["environment"],
        severity=incident["severity"],
        affected_service=incident["affected_service"],
        status=incident["status"],
        created_at=incident["created_at"],
        updated_at=incident["updated_at"],
        investigation_data=incident["investigation_data"],
        report=incident["report"]
    )


@router.get(
    "/incidents/{incident_id}/report",
    response_model=dict,
    summary="Get incident report",
    description="Get the investigation report for an incident"
)
async def get_incident_report(incident_id: str) -> dict:
    """Get the investigation report for an incident."""
    incident = incident_service.get(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )

    if not incident["report"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report available for incident {incident_id}"
        )

    return {
        "incident_id": incident_id,
        "status": incident["status"],
        "report": incident["report"],
        "generated_at": incident["updated_at"]
    }


@router.post(
    "/incidents/{incident_id}/approve",
    response_model=ApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve investigation recommendation",
    description="Submit human approval for the incident recommendation"
)
async def approve_incident(incident_id: str, approval: ApprovalRequest) -> ApprovalResponse:
    """Approve or reject the investigation recommendation."""
    incident = incident_service.get(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )

    if not incident["report"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report available for incident {incident_id}"
        )

    approved = approval.approved
    approval_status = "approved" if approved else "rejected"
    approved_at = datetime.now(timezone.utc)

    incident["report"]["approval_status"] = approval_status
    incident["report"]["approved_at"] = approved_at.isoformat()
    incident["report"]["approved_by"] = approval.approved_by or "human"
    incident["report"]["approval_comment"] = approval.comment
    incident["updated_at"] = approved_at

    if approved:
        incident["status"] = StatusEnum.RESOLVED

    incident_service.update(
        incident_id,
        status=incident["status"],
        report=incident["report"]
    )

    return ApprovalResponse(
        incident_id=incident_id,
        approved=approved,
        status=incident["status"],
        approved_at=approved_at,
        message=(
            "Recommendation approved; follow the report suggestion." if approved
            else "Recommendation rejected; further investigation is required."
        )
    )
