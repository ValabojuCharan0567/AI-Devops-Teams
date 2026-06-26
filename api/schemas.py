"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class SeverityEnum(str, Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EnvironmentEnum(str, Enum):
    """Different environments where an incident can occur."""
    PROD = "prod"
    STAGING = "staging"
    DEV = "dev"


class StatusEnum(str, Enum):
    """Possible investigation statuses for an incident."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"


class IncidentCreate(BaseModel):
    """Schema for create incident requests."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    environment: EnvironmentEnum
    severity: SeverityEnum
    affected_service: Optional[str] = Field(None, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "High CPU usage in payment service",
                "description": "Payment service pods showing 95% CPU usage for last 10 minutes",
                "environment": "prod",
                "severity": "high",
                "affected_service": "payment-service"
            }
        }


class IncidentResponse(BaseModel):
    """Schema for incident list responses."""
    id: str
    title: str
    environment: EnvironmentEnum
    severity: SeverityEnum
    status: StatusEnum
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "inc_123abc",
                "title": "High CPU usage in payment service",
                "environment": "prod",
                "severity": "high",
                "status": "in_progress",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class IncidentDetailResponse(BaseModel):
    """Schema for detailed incident responses."""
    id: str
    title: str
    description: str
    environment: EnvironmentEnum
    severity: SeverityEnum
    affected_service: Optional[str]
    status: StatusEnum
    created_at: datetime
    updated_at: datetime
    investigation_data: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "inc_123abc",
                "title": "High CPU usage in payment service",
                "description": "Payment service pods showing 95% CPU usage for last 10 minutes",
                "environment": "prod",
                "severity": "high",
                "affected_service": "payment-service",
                "status": "resolved",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T11:00:00Z",
                "investigation_data": {"logs": "...", "metrics": "..."},
                "report": "Root cause: Memory leak in cache layer..."
            }
        }


class InvestigationResult(BaseModel):
    """Schema for investigation results."""
    incident_id: str
    status: StatusEnum
    findings: Dict[str, Any]
    recommendations: List[str] = []
    timestamp: datetime

class ApprovalRequest(BaseModel):
    """Request body for approving or rejecting a recommendation."""
    approved: bool
    approved_by: Optional[str] = None
    comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response returned after human approval is submitted."""
    incident_id: str
    approved: bool
    status: StatusEnum
    approved_at: datetime
    message: str

class HealthCheck(BaseModel):
    """Schema for health check responses."""
    status: str = "healthy"
    version: str
    environment: str
