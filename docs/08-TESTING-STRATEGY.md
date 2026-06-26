# Testing Strategy & Quality Assurance

# AI DevOps Team - Testing Strategy

**Version:** 1.0

**Date:** 2026-06-26

**Prepared by:** Charan Valaboju

---

## 1. Testing Overview

### 1.1 Testing Pyramid

```
                    🔺 E2E Tests (10%)
                   User Journey Tests

              🟩🟩 Integration Tests (30%)
            Component Interaction Tests
          API Endpoint Tests

    🟨🟨🟨🟨 Unit Tests (60%)
  Function Tests
Business Logic Tests
```

### 1.2 Coverage Goals

- **Unit Tests:** 80%+ coverage
- **Integration Tests:** 70%+ coverage
- **E2E Tests:** Happy path + critical flows
- **Overall:** 85%+ code coverage

---

## 2. Unit Testing

### 2.1 Unit Test Framework

**Technology:** Pytest

**Installation:**

```bash
pip install pytest pytest-asyncio pytest-cov
```

### 2.2 Unit Tests by Module

#### 2.2.1 Log Tools Testing

**File:** `tests/unit/test_log_tools.py`

```python
import pytest
from tools.log_tools import parse_logs, calculate_severity, determine_severity

class TestParseLogsFunction:
    """Test log parsing"""

    def test_parse_logs_with_errors(self):
        logs = "2026-06-26T10:30:00 ERROR: Connection failed\n2026-06-26T10:31:00 ERROR: Timeout"
        result = parse_logs(logs)
        assert len(result) == 2
        assert all(e['keyword'] == 'error' for e in result)

    def test_parse_logs_empty(self):
        result = parse_logs("")
        assert len(result) == 0

    def test_parse_logs_no_errors(self):
        logs = "2026-06-26T10:30:00 INFO: Start\n2026-06-26T10:31:00 INFO: Complete"
        result = parse_logs(logs)
        assert len(result) == 0

class TestSeverityCalculation:
    """Test severity calculation"""

    def test_critical_severity(self):
        errors = [
            {"line": "CRITICAL: System failure", "severity": "critical"},
            {"line": "ERROR: Connection failed", "severity": "high"}
        ]
        result = calculate_severity(errors)
        assert result == "critical"

    def test_high_severity(self):
        errors = [
            {"line": "ERROR: Connection failed", "severity": "high"},
            {"line": "WARN: Slow query", "severity": "medium"}
        ]
        result = calculate_severity(errors)
        assert result == "high"

    def test_no_errors(self):
        result = calculate_severity([])
        assert result == "low"

class TestDetermineSeverityLine:
    """Test single line severity"""

    @pytest.mark.parametrize("line,expected", [
        ("FATAL: Database down", "critical"),
        ("CRITICAL: OOMKilled", "critical"),
        ("ERROR: Connection timeout", "high"),
        ("WARN: High latency", "medium"),
        ("INFO: Started", "low"),
    ])
    def test_severity_detection(self, line, expected):
        assert determine_severity(line) == expected
```

#### 2.2.2 Kubernetes Tools Testing

**File:** `tests/unit/test_kubernetes_tools.py`

```python
import pytest
from tools.kubernetes_tools import check_pods, check_deployments

class TestCheckPods:
    """Test pod checking"""

    def test_check_pods_mock_data(self):
        pods = check_pods("production")
        assert len(pods) > 0
        assert all('status' in p for p in pods)
        assert all('name' in p for p in pods)

    def test_check_pods_includes_failed(self):
        pods = check_pods("production")
        failed_pods = [p for p in pods if p['status'] != 'Running']
        assert len(failed_pods) > 0

class TestCheckDeployments:
    """Test deployment checking"""

    def test_check_deployments_mock_data(self):
        deployments = check_deployments("production")
        assert len(deployments) > 0
        assert all('replicas' in d for d in deployments)
        assert all('ready' in d for d in deployments)
```

#### 2.2.3 Pydantic Schemas Testing

**File:** `tests/unit/test_schemas.py`

```python
import pytest
from app.api.schemas import IncidentCreate, IncidentResponse
from pydantic import ValidationError

class TestIncidentCreate:
    """Test incident creation schema"""

    def test_valid_incident(self):
        data = {
            "description": "API latency issue in production",
            "environment": "production"
        }
        incident = IncidentCreate(**data)
        assert incident.description == "API latency issue in production"
        assert incident.environment == "production"

    def test_description_too_short(self):
        data = {
            "description": "Short",
            "environment": "production"
        }
        with pytest.raises(ValidationError) as exc:
            IncidentCreate(**data)
        assert "ensure this value has at least 10 characters" in str(exc.value)

    def test_description_too_long(self):
        data = {
            "description": "x" * 5001,
            "environment": "production"
        }
        with pytest.raises(ValidationError) as exc:
            IncidentCreate(**data)

    def test_invalid_environment(self):
        data = {
            "description": "Test incident description",
            "environment": "invalid"
        }
        with pytest.raises(ValidationError):
            IncidentCreate(**data)
```

### 2.3 Agent Unit Tests

**File:** `tests/unit/test_agents.py`

```python
import pytest
from agents.log_agent import LogAgent
from agents.kubernetes_agent import KubernetesAgent
from agents.report_agent import ReportAgent

class TestLogAgent:
    """Test log agent"""

    @pytest.mark.asyncio
    async def test_log_agent_with_errors(self):
        agent = LogAgent()
        task = {
            "incident": {
                "logs": "ERROR: Connection failed\nERROR: Retry failed"
            }
        }
        result = await agent.process(task)
        assert result.agent_name == "LogAgent"
        assert result.status == "success"
        assert result.severity in ["critical", "high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_log_agent_empty_logs(self):
        agent = LogAgent()
        task = {"incident": {"logs": ""}}
        result = await agent.process(task)
        assert result.status == "success"
        assert result.severity == "low"

    @pytest.mark.asyncio
    async def test_log_agent_timeout(self):
        agent = LogAgent()
        task = {"incident": {"logs": "x" * 1000000}}
        result = await agent.execute(task, timeout=0.001)
        assert result.status == "timeout"

class TestKubernetesAgent:
    """Test K8s agent"""

    @pytest.mark.asyncio
    async def test_kubernetes_agent_process(self):
        agent = KubernetesAgent()
        task = {
            "incident": {
                "kubernetes_namespace": "production"
            }
        }
        result = await agent.process(task)
        assert result.agent_name == "KubernetesAgent"
        assert result.status == "success"

class TestReportAgent:
    """Test report agent"""

    @pytest.mark.asyncio
    async def test_report_agent_process(self):
        agent = ReportAgent()
        task = {
            "incident_id": "test-123",
            "agent_results": [
                {
                    "agent_name": "LogAgent",
                    "findings": "Multiple errors detected",
                    "severity": "high"
                }
            ]
        }
        result = await agent.process(task)
        assert result.status == "success"
```

---

## 3. Integration Testing

### 3.1 API Integration Tests

**File:** `tests/integration/test_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestIncidentAPI:
    """Test incident endpoints"""

    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_create_incident(self):
        payload = {
            "description": "API latency increased in production",
            "environment": "production"
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "incident_id" in data
        assert data["status"] == "investigating"
        assert "created_at" in data

    def test_create_incident_validation_error(self):
        payload = {
            "description": "Short",
            "environment": "production"
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 422

    def test_get_incident(self):
        # Create incident
        create_payload = {
            "description": "Test incident for retrieval",
            "environment": "production"
        }
        create_response = client.post("/api/incidents", json=create_payload)
        incident_id = create_response.json()["incident_id"]

        # Get incident
        response = client.get(f"/api/incidents/{incident_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == incident_id
        assert data["status"] == "investigating" or data["status"] == "completed"

    def test_get_nonexistent_incident(self):
        response = client.get("/api/incidents/nonexistent-id")
        assert response.status_code == 404

    def test_list_incidents(self):
        response = client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data
        assert isinstance(data["incidents"], list)

    def test_list_incidents_pagination(self):
        response = client.get("/api/incidents?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
```

### 3.2 Workflow Integration Tests

**File:** `tests/integration/test_workflow.py`

```python
import pytest
from graphs.investigation_workflow import create_investigation_workflow

class TestInvestigationWorkflow:
    """Test LangGraph workflow"""

    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        workflow = create_investigation_workflow()
        state = {
            "incident": {
                "description": "Test incident",
                "logs": "ERROR: Test error",
                "kubernetes_namespace": "production",
                "environment": "production"
            },
            "agent_results": [],
            "report": {},
            "status": "submitted"
        }
        result = workflow.invoke(state)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_workflow_with_timeout(self):
        workflow = create_investigation_workflow()
        state = {
            "incident": {"description": "Test"},
            "agent_results": [],
            "report": {},
            "status": "submitted"
        }
        # Verify workflow completes within timeout
        import asyncio
        await asyncio.wait_for(
            asyncio.create_task(
                asyncio.to_thread(workflow.invoke, state)
            ),
            timeout=20
        )
```

---

## 4. End-to-End Testing

### 4.1 E2E Test Scenarios

**File:** `tests/e2e/test_scenarios.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

class TestIncidentScenarios:
    """End-to-end incident scenarios"""

    def test_production_api_latency_incident(self):
        """Complete scenario: API latency investigation"""
        # 1. Submit incident
        payload = {
            "description": "API latency increased by 300% in production",
            "logs": "ERROR: Request timeout after 30s\nERROR: Database connection failed\nERROR: Retrying...",
            "kubernetes_namespace": "production",
            "environment": "production"
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 201
        incident_id = response.json()["incident_id"]

        # 2. Wait for investigation
        time.sleep(2)

        # 3. Get investigation results
        response = client.get(f"/api/incidents/{incident_id}")
        assert response.status_code == 200
        incident = response.json()
        assert incident["status"] in ["investigating", "completed"]

        # 4. Get report
        if incident["status"] == "completed":
            response = client.get(f"/api/incidents/{incident_id}/report")
            assert response.status_code == 200
            report = response.json()
            assert "root_cause" in report
            assert "recommendations" in report

    def test_kubernetes_crash_loop_incident(self):
        """Scenario: Kubernetes pod crash loop"""
        payload = {
            "description": "Pod keeps crashing in production Kubernetes",
            "kubernetes_namespace": "production",
            "environment": "production"
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 201
        incident_id = response.json()["incident_id"]

        # Wait for investigation
        time.sleep(2)

        # Verify investigation completed
        response = client.get(f"/api/incidents/{incident_id}")
        assert response.status_code == 200
```

---

## 5. Performance Testing

### 5.1 Load Testing

**Tool:** Locust

**File:** `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        self.client.get("/api/health")

    @task(2)
    def list_incidents(self):
        self.client.get("/api/incidents")

    @task(1)
    def create_incident(self):
        self.client.post("/api/incidents", json={
            "description": "Load test incident description",
            "environment": "production"
        })
```

**Run:**

```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### 5.2 Performance Targets

| Metric                   | Target     | Tool   |
| ------------------------ | ---------- | ------ |
| API Response Time (p95)  | < 2s       | Locust |
| Investigation Time (p95) | < 20s      | Custom |
| Throughput               | > 10 req/s | Locust |

---

## 6. Test Execution

### 6.1 Run All Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests with coverage
pytest --cov=app --cov=agents --cov=tools --cov=graphs \
    --cov-report=html --cov-report=term-missing

# Run tests by category
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # E2E tests
```

### 6.2 Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── unit/
│   ├── test_log_tools.py
│   ├── test_kubernetes_tools.py
│   ├── test_schemas.py
│   └── test_agents.py
├── integration/
│   ├── test_api.py
│   └── test_workflow.py
├── e2e/
│   └── test_scenarios.py
└── performance/
    └── locustfile.py
```

### 6.3 Pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
```

---

## 7. Code Quality Tools

### 7.1 Linting

```bash
# Install
pip install pylint flake8 black

# Run pylint
pylint app/ agents/ tools/ graphs/

# Run flake8
flake8 app/ agents/ tools/ graphs/

# Format code
black app/ agents/ tools/ graphs/ tests/
```

### 7.2 Type Checking

```bash
# Install
pip install mypy

# Run mypy
mypy app/ agents/ tools/ graphs/ --strict
```

---

## 8. CI/CD Testing

### 8.1 GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install .
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 9. Test Coverage Goals

### 9.1 Coverage by Module

| Module    | V1 Target | V2 Target | V3 Target |
| --------- | --------- | --------- | --------- |
| app/api/  | 85%       | 90%       | 95%       |
| agents/   | 80%       | 90%       | 95%       |
| tools/    | 75%       | 85%       | 90%       |
| graphs/   | 70%       | 85%       | 90%       |
| services/ | 85%       | 90%       | 95%       |

---

## 10. Test Maintenance

### 10.1 Test Review Checklist

- [ ] Test name describes what it tests
- [ ] Test is independent and isolated
- [ ] Test has single responsibility
- [ ] Test includes setup and teardown
- [ ] Test has clear assertions
- [ ] Test covers happy path and errors

---

## 11. Version History

| Version | Date       | Changes                  |
| ------- | ---------- | ------------------------ |
| 1.0     | 2026-06-26 | Initial testing strategy |

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-26  
**Status:** Approved
