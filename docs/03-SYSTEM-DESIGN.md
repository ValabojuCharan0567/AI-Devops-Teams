# System Architecture & High-Level Design (HLD)

# AI DevOps Team - System Design

**Version:** 1.0

**Date:** 2026-06-26

**Prepared by:** Charan Valaboju

---

## 1. System Overview

### 1.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User/Client                             │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP(S)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Layer                                               │   │
│  │  - POST /api/incidents                                   │   │
│  │  - GET /api/incidents/{id}                               │   │
│  │  - GET /api/incidents/{id}/report                        │   │
│  │  - GET /api/health                                       │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  Service Layer                                           │   │
│  │  - IncidentService                                       │   │
│  │  - InvestigationService                                  │   │
│  │  - ReportService                                         │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
┌─────────────────────────────┴────────────────────────────────────┐
│              LangGraph Orchestration Engine                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Investigation Workflow                                  │   │
│  │  - Manager Agent (Coordinator)                           │   │
│  │  - Parallel Agent Executor                               │   │
│  │  - Result Aggregator                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
     ┌──────────▼────┐   ┌────▼──────────┐ ├──────────┐
     │                │   │               │  │         │
┌────▼──────────┐ ┌──▼───▼──────────┐  ┌─┴─▼─────────▼────┐
│ Log Analysis  │ │Kubernetes Agent │  │  GitHub Agent    │
│ Agent         │ │                 │  │ (V2)             │
└───────────────┘ └─────────────────┘  └──────────────────┘
│                │
├─────┐  ┌───────┤
│     │  │
│ ┌───▼──▼──────┐ ┌─────────────────────┐
│ │Cloud Agent  │ │Monitoring/Security  │
│ │(V2)         │ │Agents (V3)          │
│ └─────────────┘ └─────────────────────┘
│
└────────────────────┬──────────────────┐
                     │                  │
            ┌────────▼────────┐    ┌────▼──────────┐
            │ Report Agent    │    │Tool Registry   │
            │ (Aggregator)    │    │ (External APIs)│
            └────────┬────────┘    └────────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Incident Storage │
            │ (Memory / V2: DB)│
            └──────────────────┘
```

---

## 2. Component Architecture

### 2.1 Core Modules

#### API Layer (`app/api/`)

- **Purpose:** REST API endpoints
- **Components:**
  - `routes.py` - Endpoint definitions
  - `schemas.py` - Request/response validation
  - `middleware.py` - Error handling, logging
- **Technology:** FastAPI
- **Responsibilities:**
  - Request validation
  - Response formatting
  - Error handling

#### Service Layer (`app/services/`)

- **Purpose:** Business logic orchestration
- **Components:**
  - `incident_service.py` - Incident management
  - `investigation_service.py` - Investigation orchestration
  - `report_service.py` - Report generation
- **Responsibilities:**
  - Incident lifecycle management
  - Investigation workflow triggering
  - Report assembly

#### Agent Layer (`agents/`)

- **Purpose:** Specialized investigation agents
- **Components:**
  - `base_agent.py` - Abstract base agent
  - `manager_agent.py` - Orchestrator
  - `log_agent.py` - Log analysis
  - `kubernetes_agent.py` - K8s investigation
  - `github_agent.py` - Git history (V2)
  - `cloud_agent.py` - Cloud metrics (V2)
  - `monitoring_agent.py` - Prometheus/Grafana (V3)
  - `security_agent.py` - Security analysis (V3)
  - `report_agent.py` - Report generation
- **Responsibilities:**
  - Specific domain investigation
  - Tool invocation
  - Result formatting

#### Tools Layer (`tools/`)

- **Purpose:** Agent tool definitions
- **Components:**
  - `log_tools.py` - Log processing utilities
  - `kubernetes_tools.py` - K8s API interactions
  - `github_tools.py` - GitHub API calls (V2)
  - `cloud_tools.py` - AWS/Azure/GCP APIs (V2)
  - `monitoring_tools.py` - Prometheus queries (V3)
- **Responsibilities:**
  - External system interaction
  - Data retrieval
  - Error handling for external calls

#### Schemas Layer (`schemas/`)

- **Purpose:** Data models
- **Components:**
  - `incident.py` - Incident models
  - `agent.py` - Agent response models
  - `report.py` - Report models
- **Technology:** Pydantic
- **Responsibilities:**
  - Data validation
  - Type safety
  - Serialization/deserialization

---

## 3. Data Flow

### 3.1 Incident Investigation Flow

```
1. User Submits Incident
   │
   ├─→ API validates input (Pydantic schema)
   │
   ├─→ IncidentService creates incident record
   │   - Generates UUID
   │   - Records timestamp
   │   - Sets status = "investigating"
   │
   ├─→ InvestigationService triggers investigation
   │   - Calls LangGraph workflow
   │
   ├─→ LangGraph Orchestrator starts
   │   │
   │   ├─→ ManagerAgent receives incident
   │   │
   │   ├─→ ManagerAgent creates tasks for:
   │   │   - LogAgent
   │   │   - KubernetesAgent
   │   │   - (other agents based on scope)
   │   │
   │   ├─→ Agents execute in PARALLEL
   │   │   - Each agent has 10-second timeout
   │   │   - Each agent calls relevant tools
   │   │   - Each agent formats results
   │   │
   │   ├─→ Results aggregated (20-second timeout)
   │   │
   │   ├─→ ReportAgent generates report
   │   │   - Assembles evidence
   │   │   - Identifies root cause
   │   │   - Creates recommendations
   │   │
   │   └─→ ManagerAgent returns final results
   │
   ├─→ InvestigationService updates incident
   │   - Sets status = "completed"
   │   - Stores investigation_results
   │   - Stores report
   │
   └─→ API returns investigation results
```

### 3.2 Agent Execution Pattern

```
Agent Start
  │
  ├─→ Receive task from ManagerAgent
  │
  ├─→ Validate inputs
  │
  ├─→ Load tools
  │
  ├─→ Call relevant tools
  │   - Tool 1: Extract data
  │   - Tool 2: Process data
  │   - Tool 3: Generate insights
  │
  ├─→ LLM processes findings
  │   - Calls OpenAI/Gemini
  │   - Analyzes evidence
  │   - Generates conclusions
  │
  ├─→ Format response
  │   - findings: string
  │   - severity: enum
  │   - recommendations: list
  │   - execution_time: int
  │
  └─→ Return to ManagerAgent
```

---

## 4. Technology Stack

### 4.1 Backend Framework

- **FastAPI 0.100+**
  - Modern async web framework
  - Automatic API documentation
  - Built-in validation (Pydantic)
  - High performance (async/await)
  - Type hints support

### 4.2 Orchestration

- **LangGraph 0.1+**
  - Graph-based workflow engine
  - Node-based architecture
  - Built-in state management
  - Error handling and retries
  - Integrates with LangChain

### 4.3 LLM & Chains

- **LangChain 0.1+**
  - LLM abstraction layer
  - Tool/Agent framework
  - Memory management
  - Prompt templates

- **OpenAI Python Client 1.0+**
  - GPT-4 access
  - Embedding models
  - Temperature & token control

### 4.4 Data Validation

- **Pydantic 2.0+**
  - Runtime type checking
  - JSON schema generation
  - Field validators
  - Nested model support

### 4.5 Environment Management

- **python-dotenv 1.0+**
  - Load .env files
  - Secure API key management
  - Environment variable isolation

---

## 5. Agent Architecture

### 5.1 Base Agent Class

```python
class BaseAgent(ABC):
    """Abstract base for all agents"""

    @abstractmethod
    async def process(self, task: Task) -> AgentResponse:
        """Process investigation task"""
        pass

    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return agent's available tools"""
        pass

    async def execute(self, task: Task, timeout: int = 10) -> AgentResponse:
        """Execute with timeout"""
        pass
```

### 5.2 Agent Responsibilities

| Agent           | Input               | Process                 | Output                             |
| --------------- | ------------------- | ----------------------- | ---------------------------------- |
| ManagerAgent    | Incident            | Parse, plan, coordinate | Tasks assigned, results aggregated |
| LogAgent        | Raw logs            | Parse, extract errors   | Error summary, severity            |
| KubernetesAgent | Namespace           | Query API (mock)        | Pod status, health metrics         |
| GitHubAgent     | Repo                | Fetch commits, PRs      | Deployment info, changes           |
| CloudAgent      | Provider            | Query metrics           | CPU, memory, infrastructure status |
| MonitoringAgent | Prometheus endpoint | Query metrics           | Latency, error rates               |
| SecurityAgent   | Audit logs          | Analyze access          | IAM changes, anomalies             |
| ReportAgent     | All findings        | Synthesize              | Professional report                |

### 5.3 Tool Registry Pattern

```python
class ToolRegistry:
    """Centralized tool management"""

    def register_tool(self, name: str, func: Callable):
        """Register agent tool"""
        pass

    def get_tool(self, name: str) -> Callable:
        """Retrieve tool"""
        pass

    def get_agent_tools(self, agent_name: str) -> List[Tool]:
        """Get all tools for agent"""
        pass
```

---

## 6. LangGraph Workflow

### 6.1 Graph Structure

```
ENTRY_POINT
    │
    ├─→ [manager_node]
    │    - Parse incident
    │    - Create tasks
    │    │
    │    ├─→ [log_agent_node] ─┐
    │    │                       │
    │    ├─→ [k8s_agent_node] ─┬┼─→ [result_aggregator]
    │    │                      ││
    │    ├─→ [github_agent_node]─┤
    │    │                      │├─→ [report_node]
    │    └─→ [cloud_agent_node]─┘
    │
    └─→ [end_node]
```

### 6.2 Node Definitions

**Manager Node:**

- Input: Incident data
- Process: Plan investigation
- Output: Task list for agents
- Timeout: 2 seconds

**Agent Nodes (Parallel):**

- Input: Task
- Process: Execute investigation
- Output: Findings
- Timeout: 10 seconds
- Concurrency: 4 agents in parallel

**Aggregator Node:**

- Input: All agent results
- Process: Merge findings
- Output: Combined evidence
- Timeout: 2 seconds

**Report Node:**

- Input: Aggregated findings
- Process: Generate report
- Output: Professional report
- Timeout: 5 seconds

---

## 7. Error Handling Strategy

### 7.1 Agent-Level Errors

```
Agent Timeout (> 10s)
  │
  ├─→ Cancel ongoing operations
  │
  ├─→ Log timeout event
  │
  ├─→ Return partial results (if any)
  │
  └─→ Continue investigation with other agents
```

### 7.2 External Service Errors

```
External API Failure (e.g., Kubernetes)
  │
  ├─→ Catch exception
  │
  ├─→ Retry once after 1 second
  │
  ├─→ If retry fails:
  │   - Log error
  │   - Return mock data (V1) or skip this analysis
  │
  └─→ Continue investigation
```

### 7.3 LLM Errors

```
OpenAI API Error
  │
  ├─→ Check error type
  │
  ├─→ If rate limit:
  │   - Wait 2 seconds
  │   - Retry
  │
  ├─→ If authentication error:
  │   - Log error
  │   - Return error to user
  │
  └─→ If token limit exceeded:
    - Summarize findings
    - Retry with shorter input
```

---

## 8. Security Architecture

### 8.1 Input Validation

- All user inputs validated against Pydantic schemas
- String length limits enforced
- Enum validation for fixed values
- No code execution in inputs

### 8.2 API Key Management

- Stored in environment variables (`.env` file)
- Never logged or exposed in errors
- Alternative keys supported (OpenAI, Gemini)
- Rotation ready architecture

### 8.3 Logging Strategy

- Incident data logged at INFO level
- Sensitive data (API keys) never logged
- Debug logs available for troubleshooting
- Audit trail for all incident submissions

### 8.4 Future Security (V2)

- JWT token authentication
- Role-based access control
- Rate limiting
- API key encryption

---

## 9. Scalability Considerations

### 9.1 Horizontal Scaling

- Stateless API design (no in-memory state)
- FastAPI runs on multiple workers (Gunicorn)
- Investigation queue for buffering
- Load balancer distributes requests

### 9.2 Parallel Agent Execution

- LangGraph runs agents concurrently
- Non-blocking I/O for all external calls
- Asyncio-based execution
- Resource pooling for API calls

### 9.3 Future Improvements (V2+)

- Redis for distributed caching
- PostgreSQL for persistent storage
- Message queue (RabbitMQ/Kafka)
- Agent horizontal scaling

---

## 10. Deployment Architecture

### 10.1 Docker Containerization

- Single Docker image with all dependencies
- Multi-stage build for optimization
- Alpine Linux base image
- Environment variable configuration

### 10.2 Kubernetes Deployment (V2)

- Deployment manifest with replicas
- Service for load balancing
- ConfigMap for configuration
- Secrets for API keys

### 10.3 CI/CD Pipeline (V2)

- GitHub Actions for automated testing
- Automated Docker image building
- Automated deployment to K8s
- Rollback support

---

## 11. Monitoring & Observability

### 11.1 Logging

- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Cloud logging integration (V2)

### 11.2 Metrics (V2)

- Request latency
- Investigation duration
- Agent execution times
- Error rates
- Success rates

### 11.3 Tracing (V2)

- Distributed tracing for incident investigation
- Agent execution timing
- Tool call tracking

---

## 12. Development Workflow

### 12.1 Local Development

1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Copy `.env.example` to `.env`
5. Add OpenAI API key
6. Run FastAPI server: `uvicorn app.main:app --reload`
7. Access API at `http://localhost:8000`

### 12.2 Project Structure

```
ai-devops-team/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app setup
│   ├── config.py            # Configuration
│   ├── api/
│   │   ├── routes.py        # Endpoint definitions
│   │   ├── schemas.py       # Request/response validation
│   │   └── middleware.py    # Error handling
│   └── services/
│       ├── incident_service.py
│       ├── investigation_service.py
│       └── report_service.py
├── agents/
│   ├── base_agent.py
│   ├── manager_agent.py
│   ├── log_agent.py
│   ├── kubernetes_agent.py
│   └── ... (other agents)
├── tools/
│   ├── log_tools.py
│   ├── kubernetes_tools.py
│   └── ... (other tools)
├── schemas/
│   ├── incident.py
│   ├── agent.py
│   └── report.py
├── graphs/
│   └── investigation_workflow.py  # LangGraph workflow
├── tests/
│   ├── test_api.py
│   ├── test_agents.py
│   └── test_integration.py
├── docker/
│   └── Dockerfile
├── docs/
│   ├── 01-PRD.md
│   ├── 02-SRS.md
│   ├── 03-DESIGN.md
│   └── ...
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 13. Design Decisions

### Decision 1: LangGraph for Orchestration

- **Choice:** Use LangGraph instead of custom workflow engine
- **Rationale:** Purpose-built for multi-agent systems, community support, built-in error handling
- **Alternative:** Custom workflow engine (rejected - high maintenance)

### Decision 2: FastAPI for HTTP Server

- **Choice:** FastAPI instead of Flask/Django
- **Rationale:** Native async support, automatic API docs, Pydantic integration, performance
- **Alternative:** Flask (rejected - more boilerplate)

### Decision 3: Pydantic for Validation

- **Choice:** Pydantic 2.0 instead of JSON schemas
- **Rationale:** Type safety, built-in validators, error messages, IDE support
- **Alternative:** Manual validation (rejected - error-prone)

### Decision 4: Mock Kubernetes in V1

- **Choice:** Mock Kubernetes data instead of real cluster access
- **Rationale:** Portfolio focus, no infrastructure dependency, faster development
- **Timeline:** Real integration in V2

### Decision 5: Parallel Agent Execution

- **Choice:** Execute agents concurrently instead of sequentially
- **Rationale:** 4-6 second improvement in investigation time, better user experience
- **Implementation:** LangGraph native support

---

## 14. Version History

| Version | Date       | Changes               |
| ------- | ---------- | --------------------- |
| 1.0     | 2026-06-26 | Initial system design |

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-26  
**Status:** Approved
