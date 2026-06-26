from typing import Any, Dict

from langgraph import graph


InvestigationState = Dict[str, Any]


def create_investigation_workflow() -> Any:
    """Build the LangGraph workflow for a managed incident investigation."""

    async def manager_node(state: InvestigationState) -> InvestigationState:
        state["status"] = "investigating"
        state.setdefault("agent_results", [])
        return state

    async def github_node(state: InvestigationState) -> InvestigationState:
        from agents.github_agent import GitHubAgent

        agent = GitHubAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def kubernetes_node(state: InvestigationState) -> InvestigationState:
        from agents.kubernetes_agent import KubernetesAgent

        agent = KubernetesAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def aws_node(state: InvestigationState) -> InvestigationState:
        from agents.aws_agent import AWSAgent

        agent = AWSAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def metrics_node(state: InvestigationState) -> InvestigationState:
        from agents.metrics_agent import MetricsAgent

        agent = MetricsAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def cloud_node(state: InvestigationState) -> InvestigationState:
        from agents.cloud_agent import CloudAgent

        agent = CloudAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def database_node(state: InvestigationState) -> InvestigationState:
        from agents.database_agent import DatabaseAgent

        agent = DatabaseAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def slack_node(state: InvestigationState) -> InvestigationState:
        from agents.slack_agent import SlackAgent

        agent = SlackAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def network_node(state: InvestigationState) -> InvestigationState:
        from agents.network_agent import NetworkAgent

        agent = NetworkAgent()
        response = await agent.execute(state["incident"])
        state.setdefault("agent_results", []).append(response.__dict__)
        return state

    async def reviewer_node(state: InvestigationState) -> InvestigationState:
        from agents.reviewer_agent import ReviewerAgent

        agent = ReviewerAgent()
        state["aggregate"] = {
            "agent_summaries": [r["findings"] for r in state.get("agent_results", [])],
            "evidence": [item for r in state.get("agent_results", []) for item in r.get("evidence", [])]
        }
        response = await agent.execute(state)
        state.setdefault("agent_results", []).append(response.__dict__)
        state["review"] = {
            "review_text": response.findings,
            "confidence": response.details.get("confidence", 0.0),
            "confidence_source": response.details.get("confidence_source", "reviewer")
        }
        return state

    async def report_node(state: InvestigationState) -> InvestigationState:
        from agents.report_agent import ReportAgent

        agent = ReportAgent()
        report_input = {
            "aggregate": state.get("aggregate", {}),
            "review": state.get("review", {}),
            "incident": state["incident"]
        }
        response = await agent.execute(report_input)
        state["report"] = {
            "summary": response.findings,
            "confidence_estimates": response.details.get("confidence_estimates", {}),
            "recommendation": response.details.get("recommendation", "Review and approve before taking action."),
            "evidence": response.evidence
        }
        state["status"] = "completed"
        return state

    workflow = graph.StateGraph(dict)
    workflow.add_node("manager", manager_node)
    workflow.add_node("github_agent", github_node)
    workflow.add_node("kubernetes_agent", kubernetes_node)
    workflow.add_node("aws_agent", aws_node)
    workflow.add_node("metrics_agent", metrics_node)
    workflow.add_node("cloud_agent", cloud_node)
    workflow.add_node("database_agent", database_node)
    workflow.add_node("slack_agent", slack_node)
    workflow.add_node("network_agent", network_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("report", report_node)

    workflow.add_edge("manager", "github_agent")
    workflow.add_edge("github_agent", "kubernetes_agent")
    workflow.add_edge("kubernetes_agent", "aws_agent")
    workflow.add_edge("aws_agent", "metrics_agent")
    workflow.add_edge("metrics_agent", "cloud_agent")
    workflow.add_edge("cloud_agent", "database_agent")
    workflow.add_edge("database_agent", "slack_agent")
    workflow.add_edge("slack_agent", "network_agent")
    workflow.add_edge("network_agent", "reviewer")
    workflow.add_edge("reviewer", "report")

    workflow.set_entry_point("manager")
    workflow.set_finish_point("report")
    return workflow.compile(name="investigation_workflow")
