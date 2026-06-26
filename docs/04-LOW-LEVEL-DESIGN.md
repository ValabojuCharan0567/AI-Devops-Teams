# Low-Level Design (LLD) & API Specification

# AI DevOps Team - LLD
**Version:** 1.0

**Date:** 2026-06-26

**Prepared by:** Charan Valaboju

---

## 1. Class & Module Design

### 1.1 FastAPI Application Structure

#### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.config import settings

app = FastAPI(
    title="AI DevOps Team",
    description="Multi-agent AI incident investigation",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api")

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    pass

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    pass
```

#### `app/config.py`
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "AI DevOps Team"
    API_VERSION: str = "1.0.0"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TIMEOUT: int = 10
    
    # Investigation Configuration
    INVESTIGATION_TIMEOUT: int = 20
    AGENT_TIMEOUT: int = 10
    RETRY_ATTEMPTS: int = 1
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

### 1.2 API Routes & Schemas

#### `app/api/routes.py`
```python
from fastapi import APIRouter, HTTPException, status
from uuid import uuid4
from datetime import datetime
from app.api.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentDetailResponse,
    ReportResponse,
    HealthResponse
)
from app.services.incident_service import IncidentService
from app.services.investigation_service import InvestigationService
from app.services.report_service import ReportService

router = APIRouter()
incident_service = IncidentService()
investigation_service = InvestigationService()
report_service = ReportService()

@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(incident: IncidentCreate) -> IncidentResponse:
    """
    Create new incident for investigation
    
    Args:
        incident: Incident data
        
    Returns:
        Incident created response with tracking ID
        
    Raises:
        ValidationError: If input invalid
    """
    # Create incident
    incident_id = str(uuid4())
    incident_record = incident_service.create(
        incident_id=incident_id,
        description=incident.description,
        logs=incident.logs,
        kubernetes_namespace=incident.kubernetes_namespace,
        environment=incident.environment,
        created_at=datetime.utcnow()
    )
    
    # Trigger investigation (async)
    investigation_service.start_investigation(incident_id, incident)
    
    return IncidentResponse(
        incident_id=incident_id,
        status="investigating",
        created_at=incident_record.created_at
    )

@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(incident_id: str) -> IncidentDetailResponse:
    """
    Get incident details with investigation results
    
    Args:
        incident_id: Unique incident identifier
        
    Returns:
        Full incident with results
        
    Raises:
        HTTPException: 404 if incident not found
    """
    incident = incident_service.get(incident_id)
    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found"
        )
    
    return incident

@router.get("/incidents/{incident_id}/report", response_model=ReportResponse)
async def get_report(incident_id: str) -> ReportResponse:
    """
    Get generated incident report
    
    Args:
        incident_id: Unique incident identifier
        
    Returns:
        Professional incident report
        
    Raises:
        HTTPException: 404 if incident/report not found
    """
    incident = incident_service.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if not incident.report:
        raise HTTPException(status_code=202, detail="Report still generating")
    
    return incident.report

@router.get("/incidents")
async def list_incidents(limit: int = 20, offset: int = 0):
    """
    List all incidents with pagination
    
    Args:
        limit: Number of incidents to return
        offset: Pagination offset
        
    Returns:
        Paginated incident list
    """
    incidents = incident_service.list(limit=limit, offset=offset)
    return {"incidents": incidents, "limit": limit, "offset": offset}

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )
```

#### `app/api/schemas.py`
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

class EnvironmentEnum(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"

class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class StatusEnum(str, Enum):
    SUBMITTED = "submitted"
    INVESTIGATING = "investigating"
    COMPLETED = "completed"
    FAILED = "failed"

# Request Schemas
class IncidentCreate(BaseModel):
    """Schema for creating new incident"""
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Incident description"
    )
    logs: Optional[str] = Field(
        None,
        max_length=100000,
        description="Application logs"
    )
    kubernetes_namespace: Optional[str] = Field(
        None,
        regex="^[a-z0-9-]+$",
        description="Kubernetes namespace"
    )
    environment: EnvironmentEnum = Field(
        ...,
        description="Deployment environment"
    )
    
    @validator("description")
    def description_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

# Response Schemas
class IncidentResponse(BaseModel):
    """Schema for incident creation response"""
    incident_id: str
    status: StatusEnum
    created_at: datetime

class AgentFinding(BaseModel):
    """Schema for agent findings"""
    agent_name: str
    status: str
    findings: str
    severity: SeverityEnum
    recommendations: List[str]
    execution_time_ms: int

class InvestigationResults(BaseModel):
    """Schema for investigation results"""
    total_execution_time_ms: int
    agent_results: List[AgentFinding]
    aggregated_findings: str

class TimelineEvent(BaseModel):
    """Timeline event in report"""
    timestamp: str
    event: str
    severity: SeverityEnum

class ReportResponse(BaseModel):
    """Schema for incident report"""
    incident_id: str
    executive_summary: str
    root_cause: str
    timeline: List[TimelineEvent]
    evidence: List[AgentFinding]
    impact: dict
    recommendations: List[str]
    severity: SeverityEnum
    next_steps: List[str]
    generated_at: datetime

class IncidentDetailResponse(BaseModel):
    """Full incident with results"""
    incident_id: str
    status: StatusEnum
    description: str
    environment: EnvironmentEnum
    created_at: datetime
    updated_at: datetime
    investigation_results: Optional[InvestigationResults] = None
    report: Optional[ReportResponse] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
```

---

### 1.3 Service Layer

#### `app/services/incident_service.py`
```python
from typing import Dict, Optional, List
from datetime import datetime
from uuid import UUID
import json

class IncidentService:
    """Incident management service"""
    
    def __init__(self):
        # In-memory store (V1)
        # V2: Replace with database
        self.incidents: Dict[str, dict] = {}
    
    def create(self, incident_id: str, description: str, logs: Optional[str],
               kubernetes_namespace: Optional[str], environment: str,
               created_at: datetime) -> dict:
        """Create incident record"""
        incident = {
            "incident_id": incident_id,
            "status": "submitted",
            "description": description,
            "logs": logs,
            "kubernetes_namespace": kubernetes_namespace,
            "environment": environment,
            "created_at": created_at,
            "updated_at": created_at,
            "investigation_results": None,
            "report": None
        }
        self.incidents[incident_id] = incident
        return incident
    
    def get(self, incident_id: str) -> Optional[dict]:
        """Get incident by ID"""
        return self.incidents.get(incident_id)
    
    def update(self, incident_id: str, **kwargs) -> Optional[dict]:
        """Update incident"""
        if incident_id not in self.incidents:
            return None
        incident = self.incidents[incident_id]
        incident.update(kwargs)
        incident["updated_at"] = datetime.utcnow()
        return incident
    
    def list(self, limit: int = 20, offset: int = 0) -> List[dict]:
        """List incidents with pagination"""
        incidents_list = list(self.incidents.values())
        return incidents_list[offset:offset+limit]
    
    def set_investigating(self, incident_id: str):
        """Mark incident as investigating"""
        self.update(incident_id, status="investigating")
    
    def set_completed(self, incident_id: str, results: dict, report: dict):
        """Mark incident as completed"""
        self.update(
            incident_id,
            status="completed",
            investigation_results=results,
            report=report
        )
```

#### `app/services/investigation_service.py`
```python
import asyncio
from typing import Dict, Optional
from graphs.investigation_workflow import create_investigation_workflow
from app.config import settings

class InvestigationService:
    """Investigation orchestration service"""
    
    def __init__(self):
        self.workflow = create_investigation_workflow()
    
    async def start_investigation(self, incident_id: str, incident_data: dict):
        """Start investigation workflow"""
        try:
            # Execute workflow
            result = await asyncio.wait_for(
                self.workflow.invoke(
                    {"incident": incident_data},
                    config={"timeout": settings.INVESTIGATION_TIMEOUT}
                ),
                timeout=settings.INVESTIGATION_TIMEOUT
            )
            return result
        except asyncio.TimeoutError:
            return {"status": "timeout", "incident_id": incident_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

#### `app/services/report_service.py`
```python
from typing import Dict, List
from app.api.schemas import ReportResponse, AgentFinding
from datetime import datetime

class ReportService:
    """Report generation service"""
    
    def generate_report(self, incident_id: str, agent_results: List[Dict]) -> ReportResponse:
        """Generate professional incident report"""
        
        # Extract findings from agents
        findings = self._extract_findings(agent_results)
        
        # Identify root cause
        root_cause = self._identify_root_cause(findings)
        
        # Create timeline
        timeline = self._create_timeline(findings)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings, root_cause)
        
        # Determine severity
        severity = self._determine_severity(agent_results)
        
        return ReportResponse(
            incident_id=incident_id,
            executive_summary=f"Investigation found {len(agent_results)} findings.",
            root_cause=root_cause,
            timeline=timeline,
            evidence=findings,
            impact={"services_affected": 1, "users_impacted": "unknown"},
            recommendations=recommendations,
            severity=severity,
            next_steps=["Monitor closely", "Verify fix", "Update runbook"],
            generated_at=datetime.utcnow()
        )
    
    def _extract_findings(self, agent_results: List[Dict]) -> List[AgentFinding]:
        """Extract findings from agent results"""
        findings = []
        for result in agent_results:
            findings.append(AgentFinding(
                agent_name=result.get("agent_name"),
                status=result.get("status"),
                findings=result.get("findings", ""),
                severity=result.get("severity", "medium"),
                recommendations=result.get("recommendations", []),
                execution_time_ms=result.get("execution_time_ms", 0)
            ))
        return findings
    
    def _identify_root_cause(self, findings: List[AgentFinding]) -> str:
        """Identify root cause from findings"""
        # Simple heuristic: return finding with highest severity
        if findings:
            critical_findings = [f for f in findings if f.severity == "critical"]
            if critical_findings:
                return critical_findings[0].findings
            return findings[0].findings
        return "Unknown root cause"
    
    def _create_timeline(self, findings: List[AgentFinding]):
        """Create timeline of events"""
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "event": finding.findings[:100],
                "severity": finding.severity
            }
            for finding in findings
        ]
    
    def _generate_recommendations(self, findings: List[AgentFinding], root_cause: str) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        for finding in findings:
            recommendations.extend(finding.recommendations)
        return list(set(recommendations))[:5]  # Top 5 unique recommendations
    
    def _determine_severity(self, agent_results: List[Dict]) -> str:
        """Determine overall severity"""
        severities = [r.get("severity", "low") for r in agent_results]
        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        return "low"
```

---

### 1.4 Agent Architecture

#### `agents/base_agent.py`
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import time

@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    func: callable

@dataclass
class AgentResponse:
    """Agent response"""
    agent_name: str
    status: str  # success, failed, timeout
    findings: str
    severity: str
    recommendations: List[str]
    execution_time_ms: int

class BaseAgent(ABC):
    """Abstract base agent"""
    
    def __init__(self, name: str, llm_client=None):
        self.name = name
        self.llm_client = llm_client
        self.tools = self.get_tools()
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return agent's available tools"""
        pass
    
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> AgentResponse:
        """Process investigation task"""
        pass
    
    async def execute(self, task: Dict[str, Any], timeout: int = 10) -> AgentResponse:
        """Execute with timeout"""
        import asyncio
        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                self.process(task),
                timeout=timeout
            )
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result
        except asyncio.TimeoutError:
            return AgentResponse(
                agent_name=self.name,
                status="timeout",
                findings="Agent execution timed out",
                severity="high",
                recommendations=["Increase timeout", "Check agent performance"],
                execution_time_ms=timeout * 1000
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                status="failed",
                findings=f"Agent failed: {str(e)}",
                severity="medium",
                recommendations=["Check logs", "Retry investigation"],
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
```

#### `agents/manager_agent.py`
```python
from agents.base_agent import BaseAgent, Tool, AgentResponse
from typing import List, Dict, Any
import asyncio

class ManagerAgent(BaseAgent):
    """Orchestrator agent"""
    
    def __init__(self, llm_client=None, agent_registry=None):
        super().__init__("ManagerAgent", llm_client)
        self.agent_registry = agent_registry or {}
    
    def get_tools(self) -> List[Tool]:
        """Manager tools"""
        return [
            Tool(
                name="coordinate_agents",
                description="Coordinate other agents",
                func=self._coordinate_agents
            )
        ]
    
    async def process(self, task: Dict[str, Any]) -> AgentResponse:
        """Orchestrate investigation"""
        incident = task.get("incident", {})
        
        # Determine which agents to use
        agents_to_use = self._determine_agents(incident)
        
        # Create tasks for each agent
        agent_tasks = {}
        for agent_name in agents_to_use:
            agent_tasks[agent_name] = {
                "incident": incident,
                "agent_name": agent_name
            }
        
        # Execute agents in parallel
        results = await self._execute_agents_parallel(agent_tasks)
        
        # Aggregate findings
        findings = self._aggregate_findings(results)
        
        return AgentResponse(
            agent_name="ManagerAgent",
            status="success",
            findings=findings,
            severity="high" if any(r["severity"] == "critical" for r in results) else "medium",
            recommendations=[],
            execution_time_ms=0
        )
    
    def _determine_agents(self, incident: Dict) -> List[str]:
        """Determine which agents to use"""
        agents = ["LogAgent"]
        if incident.get("kubernetes_namespace"):
            agents.append("KubernetesAgent")
        return agents
    
    async def _execute_agents_parallel(self, tasks: Dict[str, Dict]) -> List[Dict]:
        """Execute agents in parallel"""
        futures = {}
        for agent_name, task in tasks.items():
            if agent_name in self.agent_registry:
                agent = self.agent_registry[agent_name]
                futures[agent_name] = asyncio.create_task(
                    agent.execute(task, timeout=10)
                )
        
        results = []
        for agent_name, future in futures.items():
            try:
                result = await future
                results.append(result.__dict__)
            except Exception as e:
                results.append({
                    "agent_name": agent_name,
                    "status": "error",
                    "findings": str(e)
                })
        return results
    
    def _aggregate_findings(self, results: List[Dict]) -> str:
        """Aggregate all findings"""
        return " | ".join([r.get("findings", "") for r in results])
```

#### `agents/log_agent.py`
```python
from agents.base_agent import BaseAgent, Tool, AgentResponse
from typing import List, Dict, Any
from tools.log_tools import parse_logs, calculate_severity

class LogAgent(BaseAgent):
    """Log analysis agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("LogAgent", llm_client)
    
    def get_tools(self) -> List[Tool]:
        """Log agent tools"""
        return [
            Tool(
                name="parse_logs",
                description="Parse application logs",
                func=parse_logs
            ),
            Tool(
                name="calculate_severity",
                description="Calculate error severity",
                func=calculate_severity
            )
        ]
    
    async def process(self, task: Dict[str, Any]) -> AgentResponse:
        """Analyze logs"""
        incident = task.get("incident", {})
        logs = incident.get("logs", "")
        
        if not logs:
            return AgentResponse(
                agent_name="LogAgent",
                status="success",
                findings="No logs provided",
                severity="low",
                recommendations=["Provide logs for analysis"],
                execution_time_ms=0
            )
        
        # Parse logs
        errors = parse_logs(logs)
        
        # Calculate severity
        severity = calculate_severity(errors)
        
        return AgentResponse(
            agent_name="LogAgent",
            status="success",
            findings=f"Found {len(errors)} errors in logs",
            severity=severity,
            recommendations=["Check error details", "Review stack traces"],
            execution_time_ms=0
        )
```

#### `agents/kubernetes_agent.py`
```python
from agents.base_agent import BaseAgent, Tool, AgentResponse
from typing import List, Dict, Any
from tools.kubernetes_tools import check_pods, check_deployments

class KubernetesAgent(BaseAgent):
    """Kubernetes cluster investigation"""
    
    def __init__(self, llm_client=None):
        super().__init__("KubernetesAgent", llm_client)
    
    def get_tools(self) -> List[Tool]:
        """K8s tools"""
        return [
            Tool(
                name="check_pods",
                description="Check pod status",
                func=check_pods
            ),
            Tool(
                name="check_deployments",
                description="Check deployment status",
                func=check_deployments
            )
        ]
    
    async def process(self, task: Dict[str, Any]) -> AgentResponse:
        """Check Kubernetes cluster"""
        incident = task.get("incident", {})
        namespace = incident.get("kubernetes_namespace", "default")
        
        # Check pods
        pods = check_pods(namespace)
        
        # Check deployments
        deployments = check_deployments(namespace)
        
        return AgentResponse(
            agent_name="KubernetesAgent",
            status="success",
            findings=f"Checked {len(pods)} pods in {namespace}",
            severity="medium",
            recommendations=["Scale up replicas", "Check resource limits"],
            execution_time_ms=0
        )
```

#### `agents/report_agent.py`
```python
from agents.base_agent import BaseAgent, Tool, AgentResponse
from typing import List, Dict, Any

class ReportAgent(BaseAgent):
    """Report generation agent"""
    
    def __init__(self, llm_client=None, report_service=None):
        super().__init__("ReportAgent", llm_client)
        self.report_service = report_service
    
    def get_tools(self) -> List[Tool]:
        """Report tools"""
        return []
    
    async def process(self, task: Dict[str, Any]) -> AgentResponse:
        """Generate professional report"""
        agent_results = task.get("agent_results", [])
        incident_id = task.get("incident_id")
        
        if self.report_service:
            report = self.report_service.generate_report(incident_id, agent_results)
            return AgentResponse(
                agent_name="ReportAgent",
                status="success",
                findings=f"Report generated: {report.executive_summary}",
                severity="low",
                recommendations=[],
                execution_time_ms=0
            )
        
        return AgentResponse(
            agent_name="ReportAgent",
            status="success",
            findings="Report template ready",
            severity="low",
            recommendations=[],
            execution_time_ms=0
        )
```

---

### 1.5 Tools Layer

#### `tools/log_tools.py`
```python
from typing import List, Dict

def parse_logs(logs: str) -> List[Dict]:
    """Parse logs and extract errors"""
    error_keywords = ["error", "exception", "fatal", "critical", "fail"]
    errors = []
    
    for line in logs.split("\n"):
        for keyword in error_keywords:
            if keyword.lower() in line.lower():
                errors.append({
                    "line": line.strip(),
                    "keyword": keyword,
                    "severity": determine_severity(line)
                })
                break
    
    return errors

def determine_severity(line: str) -> str:
    """Determine severity from log line"""
    line_lower = line.lower()
    if "fatal" in line_lower or "critical" in line_lower:
        return "critical"
    elif "error" in line_lower:
        return "high"
    elif "warn" in line_lower:
        return "medium"
    return "low"

def calculate_severity(errors: List[Dict]) -> str:
    """Calculate overall severity"""
    if not errors:
        return "low"
    severities = [e["severity"] for e in errors]
    if "critical" in severities:
        return "critical"
    elif "high" in severities:
        return "high"
    elif "medium" in severities:
        return "medium"
    return "low"
```

#### `tools/kubernetes_tools.py`
```python
from typing import List, Dict

def check_pods(namespace: str) -> List[Dict]:
    """Check pod status (mock implementation for V1)"""
    # Mock data for MVP
    return [
        {"name": "api-pod-1", "status": "Running", "restarts": 0},
        {"name": "api-pod-2", "status": "Running", "restarts": 0},
        {"name": "cache-pod-1", "status": "CrashLoopBackOff", "restarts": 5},
    ]

def check_deployments(namespace: str) -> List[Dict]:
    """Check deployment status (mock implementation for V1)"""
    return [
        {"name": "api", "replicas": 2, "ready": 2},
        {"name": "cache", "replicas": 1, "ready": 0},
    ]
```

---

## 2. API Endpoints Detailed Specification

### 2.1 Create Incident

**Endpoint:** `POST /api/incidents`

**Authentication:** None (V1)

**Request Body:**
```json
{
  "description": "API latency increased by 300% in production",
  "logs": "2026-06-26T10:30:00 ERROR: Request timeout after 30s\n2026-06-26T10:31:00 ERROR: Connection pool exhausted",
  "kubernetes_namespace": "production",
  "environment": "production"
}
```

**Response (201 Created):**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "investigating",
  "created_at": "2026-06-26T10:30:00.000Z"
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "description"],
      "msg": "ensure this value has at least 10 characters",
      "type": "value_error.string.too_short"
    }
  ]
}
```

---

### 2.2 Get Incident

**Endpoint:** `GET /api/incidents/{incident_id}`

**Authentication:** None (V1)

**Path Parameters:**
- `incident_id` (string, required): UUID of incident

**Response (200 OK):**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "description": "API latency increased by 300%",
  "environment": "production",
  "created_at": "2026-06-26T10:30:00.000Z",
  "updated_at": "2026-06-26T10:30:15.000Z",
  "investigation_results": {
    "total_execution_time_ms": 8450,
    "agent_results": [
      {
        "agent_name": "LogAgent",
        "status": "success",
        "findings": "Found 5 timeout errors in logs",
        "severity": "high",
        "recommendations": ["Increase timeout", "Scale horizontally"],
        "execution_time_ms": 2340
      }
    ],
    "aggregated_findings": "Multiple timeout errors detected"
  },
  "report": {
    "incident_id": "550e8400-e29b-41d4-a716-446655440000",
    "executive_summary": "Investigation identified connection pool exhaustion.",
    "root_cause": "Database connection pool limit reached",
    "timeline": [
      {
        "timestamp": "2026-06-26T10:30:00.000Z",
        "event": "First timeout error detected",
        "severity": "high"
      }
    ],
    "evidence": [...],
    "impact": {"services_affected": 1, "users_impacted": "50%"},
    "recommendations": ["Scale database connections", "Implement connection pooling"],
    "severity": "high",
    "next_steps": ["Monitor connections", "Verify fix", "Update runbook"],
    "generated_at": "2026-06-26T10:30:15.000Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Incident 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

### 2.3 Get Report

**Endpoint:** `GET /api/incidents/{incident_id}/report`

**Authentication:** None (V1)

**Response (200 OK):** See Report Response model

**Response (202 Accepted):**
```json
{
  "detail": "Report still generating"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Incident not found"
}
```

---

### 2.4 List Incidents

**Endpoint:** `GET /api/incidents`

**Authentication:** None (V1)

**Query Parameters:**
- `limit` (integer, optional, default=20): Number of incidents
- `offset` (integer, optional, default=0): Pagination offset

**Response (200 OK):**
```json
{
  "incidents": [
    {
      "incident_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "description": "API latency increased",
      ...
    }
  ],
  "limit": 20,
  "offset": 0
}
```

---

### 2.5 Health Check

**Endpoint:** `GET /api/health`

**Authentication:** None

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-26T10:30:00.000Z"
}
```

---

## 3. LangGraph Workflow Definition

#### `graphs/investigation_workflow.py`
```python
from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
import asyncio

class InvestigationState(TypedDict):
    """Investigation workflow state"""
    incident: Dict[str, Any]
    agent_results: List[Dict]
    report: Dict
    status: str

def create_investigation_workflow():
    """Create LangGraph workflow"""
    
    def manager_node(state: InvestigationState) -> InvestigationState:
        """Manager coordinates investigation"""
        state["status"] = "investigating"
        return state
    
    def log_agent_node(state: InvestigationState) -> InvestigationState:
        """Log analysis"""
        # Execute log agent
        return state
    
    def k8s_agent_node(state: InvestigationState) -> InvestigationState:
        """Kubernetes investigation"""
        # Execute K8s agent
        return state
    
    def aggregator_node(state: InvestigationState) -> InvestigationState:
        """Aggregate results"""
        state["status"] = "reporting"
        return state
    
    def report_node(state: InvestigationState) -> InvestigationState:
        """Generate report"""
        state["status"] = "completed"
        return state
    
    # Create graph
    workflow = StateGraph(InvestigationState)
    
    # Add nodes
    workflow.add_node("manager", manager_node)
    workflow.add_node("log_agent", log_agent_node)
    workflow.add_node("k8s_agent", k8s_agent_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("report", report_node)
    
    # Add edges
    workflow.add_edge("manager", "log_agent")
    workflow.add_edge("manager", "k8s_agent")
    workflow.add_edge("log_agent", "aggregator")
    workflow.add_edge("k8s_agent", "aggregator")
    workflow.add_edge("aggregator", "report")
    
    # Set entry/exit
    workflow.set_entry_point("manager")
    workflow.set_finish_point("report")
    
    return workflow.compile()
```

---

## 4. Error Handling Specification

### 4.1 HTTP Error Responses

**400 Bad Request:**
- Invalid JSON in request body
- Missing required fields

**404 Not Found:**
- Incident ID doesn't exist
- Report not generated yet

**422 Unprocessable Entity:**
- Validation error (invalid enum value, string length)
- Malformed input data

**500 Internal Server Error:**
- Unexpected server error
- Uncaught exception

---

## 5. Testing Strategy

### 5.1 Unit Tests

```python
# tests/test_log_agent.py
import pytest
from agents.log_agent import LogAgent

@pytest.mark.asyncio
async def test_log_agent_process():
    agent = LogAgent()
    task = {
        "incident": {
            "logs": "ERROR: Connection failed\nERROR: Retry attempt 1"
        }
    }
    result = await agent.process(task)
    assert result.status == "success"
    assert result.severity in ["critical", "high", "medium", "low"]

@pytest.mark.asyncio
async def test_log_agent_empty_logs():
    agent = LogAgent()
    task = {"incident": {"logs": ""}}
    result = await agent.process(task)
    assert result.status == "success"
    assert result.severity == "low"
```

### 5.2 Integration Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_incident():
    response = client.post("/api/incidents", json={
        "description": "Test incident description",
        "environment": "production"
    })
    assert response.status_code == 201
    assert "incident_id" in response.json()

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## 6. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-26 | Initial LLD |

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-26  
**Status:** Approved
