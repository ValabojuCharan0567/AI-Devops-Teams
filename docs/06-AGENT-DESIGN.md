# Agent Design Document

# AI DevOps Team - Agent Design
**Version:** 1.0

**Date:** 2026-06-26

**Prepared by:** Charan Valaboju

---

## 1. Agent Architecture Overview

### 1.1 Agent Types

| Agent | Scope | V | Status |
|-------|-------|---|--------|
| Manager | Orchestrator | 1 | MVP |
| Log Analysis | Error detection | 1 | MVP |
| Kubernetes | Cluster health | 1 | MVP (mock) |
| GitHub | Deployment history | 2 | Future |
| Cloud | Infrastructure metrics | 2 | Future |
| Monitoring | Prometheus/Grafana | 3 | Future |
| Security | IAM/anomaly detection | 3 | Future |
| Report | Report generation | 1 | MVP |

---

## 2. Manager Agent (Orchestrator)

### 2.1 Responsibilities
- Parse incident description
- Determine investigation scope
- Create task assignments
- Coordinate parallel agent execution
- Aggregate results
- Orchestrate report generation

### 2.2 Inputs

```json
{
  "incident": {
    "description": "API latency spike in production",
    "logs": "...log data...",
    "kubernetes_namespace": "production",
    "environment": "production"
  }
}
```

### 2.3 Outputs

```json
{
  "agent_name": "ManagerAgent",
  "status": "success",
  "findings": "Coordinated investigation across 3 agents",
  "severity": "high",
  "recommendations": [],
  "execution_time_ms": 8450,
  "assigned_tasks": [
    {"agent": "LogAgent", "task": "analyze_logs"},
    {"agent": "KubernetesAgent", "task": "check_cluster"}
  ]
}
```

### 2.4 Decision Logic

```
Manager Agent Decision Tree:

Incident received
├─ Analyze description
├─ Determine scope:
│  ├─ Has logs? → Assign LogAgent
│  ├─ Has K8s namespace? → Assign KubernetesAgent
│  ├─ Mentions "deployment"? → Assign GitHubAgent (V2)
│  ├─ Mentions "cloud/AWS"? → Assign CloudAgent (V2)
│  └─ Production environment? → Assign SecurityAgent (V3)
│
└─ Execute assigned agents in parallel
   ├─ Set timeout: 10 seconds per agent
   ├─ Collect results
   └─ Aggregate findings
```

### 2.5 Prompts

**System Prompt:**
```
You are the ManagerAgent, responsible for coordinating a team of specialized 
DevOps investigation agents.

Your responsibilities:
1. Understand the incident description
2. Determine which agents should investigate
3. Create focused tasks for each agent
4. Coordinate parallel execution
5. Synthesize findings into actionable insights

Be concise and methodical. Focus on identifying the most likely root cause.
```

**User Prompt Template:**
```
An incident has been reported:

Description: {description}
Environment: {environment}
Namespace: {namespace}

Determine which agents should investigate and why. Consider:
- Are there logs to analyze?
- Is Kubernetes involved?
- Has there been a recent deployment?
- Could this be a security issue?
```

---

## 3. Log Analysis Agent

### 3.1 Responsibilities
- Parse application logs
- Detect error patterns
- Calculate severity
- Identify root causes
- Suggest remediation steps

### 3.2 Inputs

```json
{
  "incident": {
    "logs": "2026-06-26T10:30:00 ERROR Connection failed\n2026-06-26T10:31:00 ERROR Retry attempt failed\n..."
  }
}
```

### 3.3 Outputs

```json
{
  "agent_name": "LogAgent",
  "status": "success",
  "findings": "Found 15 error lines. Pattern: Connection timeouts. Frequency: Every 30 seconds.",
  "severity": "high",
  "recommendations": [
    "Increase connection pool size",
    "Check downstream service health",
    "Review network connectivity",
    "Scale backend instances"
  ],
  "execution_time_ms": 2340
}
```

### 3.4 Analysis Algorithm

```
Log Analysis Algorithm:

1. Parse logs
   ├─ Split by newline
   ├─ Extract timestamp, level, message
   └─ Store in structured format

2. Error Detection
   ├─ Search for keywords: ERROR, FATAL, CRITICAL, EXCEPTION
   ├─ Extract full stack traces
   ├─ Group by error type
   └─ Count frequency

3. Pattern Recognition
   ├─ Identify error clusters (time-based)
   ├─ Calculate frequency
   ├─ Detect escalation patterns
   └─ Find correlations

4. Severity Calculation
   ├─ If FATAL/CRITICAL → severity = critical
   ├─ Else if ERROR count > 10 → severity = high
   ├─ Else if WARN count > 20 → severity = medium
   └─ Else → severity = low

5. Generate Recommendations
   ├─ Match error pattern to known solutions
   ├─ Suggest scaling if resource errors
   ├─ Suggest retry/timeout if timeout errors
   └─ Suggest monitoring if intermittent
```

### 3.5 Tool Functions

**Tool: parse_logs**
```python
def parse_logs(logs: str) -> List[LogEntry]:
    """Parse logs into structured format"""
    # Implementation in tools/log_tools.py
    pass

# Returns:
[
  {
    "timestamp": "2026-06-26T10:30:00",
    "level": "ERROR",
    "message": "Connection failed",
    "source": "database"
  },
  ...
]
```

**Tool: calculate_severity**
```python
def calculate_severity(errors: List[LogEntry]) -> str:
    """Calculate severity from error patterns"""
    # Implementation in tools/log_tools.py
    pass

# Returns: "critical", "high", "medium", or "low"
```

### 3.6 Prompts

**System Prompt:**
```
You are the LogAgent, responsible for analyzing application logs to identify issues.

Your expertise:
- Parsing and understanding application logs
- Identifying error patterns and anomalies
- Calculating severity and impact
- Suggesting specific remediation steps

Provide clear, actionable findings based on log evidence.
```

**User Prompt Template:**
```
Analyze these logs and identify the root cause:

{parsed_logs}

Error summary: {error_count} errors, {unique_error_types} unique types
Severity: {severity}

Provide:
1. What errors occurred?
2. When did they start?
3. How frequently?
4. What's the likely root cause?
5. Recommended actions?
```

---

## 4. Kubernetes Agent (Mock V1, Real V2)

### 4.1 Responsibilities
- Check pod status
- Analyze resource usage
- Identify deployment issues
- Detect restart loops
- Suggest scaling actions

### 4.2 Inputs

```json
{
  "incident": {
    "kubernetes_namespace": "production"
  }
}
```

### 4.3 Outputs

```json
{
  "agent_name": "KubernetesAgent",
  "status": "success",
  "findings": "Pod cache-1 in CrashLoopBackOff. 12 restarts in 10 minutes. Memory usage at 95%.",
  "severity": "critical",
  "recommendations": [
    "Increase memory limit for cache pod",
    "Check pod logs for OOM killer",
    "Consider horizontal scaling",
    "Review recent deployment changes"
  ],
  "execution_time_ms": 1850
}
```

### 4.4 K8s Analysis Algorithm

```
Kubernetes Analysis:

1. Fetch Pod Status
   ├─ Query API for all pods in namespace
   ├─ Get status: Running, Pending, Failed, CrashLoopBackOff
   ├─ Count by status
   └─ Identify unhealthy pods

2. Analyze Resource Usage
   ├─ Get current CPU usage
   ├─ Get current memory usage
   ├─ Compare to requested/limits
   ├─ Identify bottlenecks
   └─ Calculate utilization %

3. Check Pod Restarts
   ├─ Get restart count per pod
   ├─ Identify pods with high restarts
   ├─ Calculate restart rate (restarts/time)
   ├─ Flag if restart rate > threshold
   └─ Extract last restart reason

4. Check Deployments
   ├─ Get desired replicas
   ├─ Get ready replicas
   ├─ Flag if mismatch
   ├─ Check recent rollouts
   └─ Identify outdated replicas

5. Severity Assessment
   ├─ If CrashLoopBackOff → critical
   ├─ Else if pending pods → high
   ├─ Else if resource usage > 90% → high
   ├─ Else if restarts increasing → medium
   └─ Else → low

6. Generate Recommendations
   ├─ If memory high: increase limit
   ├─ If CPU high: add replicas or optimize
   ├─ If CrashLoopBackOff: check logs
   ├─ If pending: check node resources
   └─ If recent deployment: consider rollback
```

### 4.5 V1 Mock Data

```python
def check_pods_mock(namespace: str) -> List[Dict]:
    """Mock pod status for MVP"""
    return [
        {
            "name": "api-pod-1",
            "namespace": namespace,
            "status": "Running",
            "restarts": 0,
            "cpu_usage": "45%",
            "memory_usage": "62%",
            "ready": True
        },
        {
            "name": "api-pod-2",
            "status": "Running",
            "restarts": 0,
            "cpu_usage": "42%",
            "memory_usage": "58%",
            "ready": True
        },
        {
            "name": "cache-pod-1",
            "status": "CrashLoopBackOff",
            "restarts": 12,
            "cpu_usage": "N/A",
            "memory_usage": "N/A",
            "ready": False,
            "last_reason": "OOMKilled"
        }
    ]
```

### 4.6 V2 Real Implementation

```python
from kubernetes import client, config, watch

def check_pods_real(namespace: str) -> List[Dict]:
    """Real K8s cluster check"""
    config.load_incluster_config()  # or load_kube_config()
    v1 = client.CoreV1Api()
    
    pods = v1.list_namespaced_pod(namespace)
    # Process and return pod details
```

### 4.7 Prompts

**System Prompt:**
```
You are the KubernetesAgent, expert in Kubernetes cluster debugging.

Your expertise:
- Pod lifecycle and health
- Resource management and scaling
- Deployment strategies
- Troubleshooting cluster issues

Provide concise findings based on cluster state.
```

---

## 5. Report Agent

### 5.1 Responsibilities
- Compile all findings
- Synthesize root cause
- Create professional report
- Generate actionable recommendations
- Format output

### 5.2 Inputs

```json
{
  "incident_id": "550e8400...",
  "agent_results": [
    {
      "agent_name": "LogAgent",
      "findings": "..."
    },
    {
      "agent_name": "KubernetesAgent",
      "findings": "..."
    }
  ]
}
```

### 5.3 Outputs

```json
{
  "executive_summary": "Investigation identified cache service memory exhaustion as root cause.",
  "root_cause": "Cache pod memory limit insufficient for current dataset size",
  "timeline": [...],
  "evidence": [...],
  "recommendations": [...],
  "severity": "critical"
}
```

### 5.4 Report Generation Algorithm

```
Report Generation:

1. Extract Key Findings
   ├─ Identify critical issues from all agents
   ├─ Rank by severity
   ├─ Extract recommendations
   └─ Collect evidence

2. Synthesize Root Cause
   ├─ Find common patterns
   ├─ Identify primary cause vs symptoms
   ├─ Cross-reference agent findings
   └─ Generate coherent narrative

3. Create Timeline
   ├─ Extract timestamps from logs
   ├─ Order events chronologically
   ├─ Identify escalation points
   └─ Mark key transitions

4. Assess Impact
   ├─ Affected services
   ├─ User impact estimate
   ├─ Business impact
   └─ Duration of incident

5. Generate Recommendations
   ├─ Immediate mitigation steps
   ├─ Short-term fixes
   ├─ Long-term improvements
   └─ Preventive measures

6. Format Report
   ├─ Professional tone
   ├─ Clear sections
   ├─ Actionable items
   └─ Executive friendly
```

### 5.5 Prompts

**System Prompt:**
```
You are the ReportAgent, responsible for synthesizing investigation findings 
into clear, professional incident reports.

Your task:
- Combine findings from all agents
- Identify the root cause
- Create a clear narrative
- Provide actionable recommendations
- Format for both technical and non-technical audiences

Be professional, precise, and action-oriented.
```

**User Prompt Template:**
```
Create an incident report based on these findings:

Agent Results:
{agent_results_formatted}

Overall Severity: {severity}
Environment: {environment}
Incident Duration: {duration}

Generate a report including:
1. Executive Summary (2-3 sentences, manager-friendly)
2. Root Cause (technical, specific)
3. Timeline (chronological events)
4. Impact Assessment
5. Recommendations (actionable steps)
6. Next Steps
```

---

## 6. Future Agents (V2+)

### 6.1 GitHub Agent (V2)

**Responsibilities:**
- Fetch recent commits
- Check deployments
- Identify changed services
- Analyze PRs
- Link code changes to incident

**Tools:**
- `get_recent_commits(repo, branch, count=20)`
- `get_deployments(repo, environment)`
- `get_changed_files(commit_range)`
- `analyze_pull_requests(repo)`

### 6.2 Cloud Agent (V2)

**Responsibilities:**
- Query AWS/Azure/GCP metrics
- Analyze CPU/memory/network
- Check infrastructure issues
- Identify scaling issues

**Supported Providers:**
- AWS CloudWatch
- Azure Monitor
- Google Cloud Monitoring

### 6.3 Monitoring Agent (V3)

**Responsibilities:**
- Query Prometheus metrics
- Analyze Grafana dashboards
- Detect latency spikes
- Track error rates

### 6.4 Security Agent (V3)

**Responsibilities:**
- Review IAM changes
- Detect suspicious activity
- Analyze firewall changes
- Identify anomalies

---

## 7. Agent Communication Protocol

### 7.1 Task Format

```python
@dataclass
class Task:
    agent_name: str
    task_type: str  # analyze, query, check
    incident_data: Dict[str, Any]
    timeout: int = 10
    retry_on_error: bool = True
```

### 7.2 Response Format

```python
@dataclass
class AgentResponse:
    agent_name: str
    status: str  # success, failed, timeout
    findings: str
    severity: str
    recommendations: List[str]
    execution_time_ms: int
    metadata: Dict[str, Any]
```

---

## 8. Error Handling

### 8.1 Agent Timeout
- Default: 10 seconds
- Action: Return partial results
- Logging: Log timeout event

### 8.2 External API Failure
- Action: Retry once
- Fallback: Return mock/cached data
- Logging: Log error

### 8.3 LLM Error
- Rate limit: Retry with backoff
- Token limit: Summarize and retry
- Auth error: Return error to user

---

## 9. Agent Testing

### 9.1 Unit Tests
```python
@pytest.mark.asyncio
async def test_log_agent_finds_errors():
    agent = LogAgent()
    task = {"incident": {"logs": "ERROR: Connection failed"}}
    result = await agent.process(task)
    assert result.severity == "high"
```

### 9.2 Integration Tests
```python
@pytest.mark.asyncio
async def test_manager_coordinates_agents():
    manager = ManagerAgent(agent_registry={...})
    result = await manager.process({"incident": {...}})
    assert result.status == "success"
```

---

## 10. Agent Performance

### 10.1 Execution Targets
- LogAgent: < 3 seconds
- KubernetesAgent: < 2 seconds
- Report Agent: < 5 seconds
- Manager Agent: < 20 seconds total

### 10.2 Metrics to Track
- Execution time
- Success rate
- Error rate
- LLM token usage

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-26 | Initial agent design |

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-26  
**Status:** Approved
