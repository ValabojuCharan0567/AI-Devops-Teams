from typing import Any, Dict, List

import requests

from app.config import settings


def query_prometheus(query: str, timeout: int = 10) -> Dict[str, Any]:
    url = settings.prometheus_url.rstrip("/") + "/api/v1/query"
    response = requests.get(url, params={"query": query}, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_monitoring_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    evidence: List[str] = []
    results: Dict[str, Any] = {}

    if not settings.prometheus_url:
        return {
            "prometheus_url": settings.prometheus_url,
            "grafana_url": settings.grafana_url,
            "service": incident.get("affected_service"),
            "evidence": ["Prometheus URL is not configured; skipping monitoring activity."],
            "results": {}
        }

    service = incident.get("affected_service")
    label_selector = f',service="{service}"' if service else ""

    queries = {
        "95th_latency": f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{{label_selector}}}[5m])) by (le))',
        "error_rate": f'sum(rate(http_requests_total{{{label_selector},status=~"5.."}}[5m]))',
        "up_status": f'sum(up{{{label_selector}}})'
    }

    for key, query in queries.items():
        try:
            data = query_prometheus(query)
            results[key] = data.get("data", {}).get("result", [])
            count = len(results[key])
            evidence.append(f"Prometheus query '{key}' returned {count} result(s)")
        except requests.RequestException as exc:
            results[key] = {"error": str(exc)}
            evidence.append(f"Prometheus '{key}' query failed: {exc}")
        except Exception as exc:
            results[key] = {"error": str(exc)}
            evidence.append(f"Prometheus '{key}' unexpected error: {exc}")

    if settings.grafana_url and settings.grafana_api_key:
        grafana_url = settings.grafana_url.rstrip("/") + "/api/search"
        headers = {"Authorization": f"Bearer {settings.grafana_api_key}"}
        try:
            response = requests.get(grafana_url, headers=headers, timeout=10)
            response.raise_for_status()
            dashboards = response.json()
            evidence.append(f"Grafana returned {len(dashboards)} dashboards")
            results["grafana_dashboards"] = dashboards
        except requests.RequestException as exc:
            results["grafana_error"] = str(exc)
            evidence.append(f"Grafana query failed: {exc}")
        except Exception as exc:
            results["grafana_error"] = str(exc)
            evidence.append(f"Grafana unexpected error: {exc}")
    else:
        evidence.append("Grafana is not configured; skipping dashboard discovery.")

    if not evidence:
        evidence.append("No monitoring evidence was produced.")

    return {
        "prometheus_url": settings.prometheus_url,
        "grafana_url": settings.grafana_url,
        "service": service,
        "evidence": evidence,
        "results": results
    }


def fetch_network_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    evidence: List[str] = []
    results: Dict[str, Any] = {}

    if not settings.prometheus_url:
        return {
            "prometheus_url": settings.prometheus_url,
            "service": incident.get("affected_service"),
            "evidence": ["Prometheus URL is not configured; skipping network activity."],
            "results": {}
        }

    service = incident.get("affected_service")
    label_selector = f',service="{service}"' if service else ""

    queries = {
        "network_receive_rate": f'sum(rate(node_network_receive_bytes_total{{{label_selector}}}[5m]))',
        "network_transmit_rate": f'sum(rate(node_network_transmit_bytes_total{{{label_selector}}}[5m]))',
        "network_error_count": f'sum(rate(node_network_receive_errs_total{{{label_selector}}}[5m]) + rate(node_network_transmit_errs_total{{{label_selector}}}[5m]))'
    }

    for key, query in queries.items():
        try:
            data = query_prometheus(query)
            results[key] = data.get("data", {}).get("result", [])
            count = len(results[key])
            evidence.append(f"Prometheus network query '{key}' returned {count} result(s)")
        except requests.RequestException as exc:
            results[key] = {"error": str(exc)}
            evidence.append(f"Prometheus network query '{key}' failed: {exc}")
        except Exception as exc:
            results[key] = {"error": str(exc)}
            evidence.append(f"Prometheus network query '{key}' unexpected error: {exc}")

    if not evidence:
        evidence.append("No network evidence was produced.")

    return {
        "prometheus_url": settings.prometheus_url,
        "service": service,
        "evidence": evidence,
        "results": results
    }
