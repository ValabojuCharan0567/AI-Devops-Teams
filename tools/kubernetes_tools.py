from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from kubernetes import client, config
from kubernetes.client import ApiException

from app.config import settings


def load_kube() -> None:
    try:
        if settings.kubernetes_kubeconfig:
            config.load_kube_config(config_file=settings.kubernetes_kubeconfig)
        else:
            config.load_kube_config()
    except Exception:
        config.load_incluster_config()


def fetch_kubernetes_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    namespace = settings.kubernetes_namespace or "default"
    evidence: List[str] = []
    pods = []
    events = []

    try:
        load_kube()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace=namespace)
        events = v1.list_namespaced_event(namespace=namespace)
    except Exception as exc:
        return {
            "namespace": namespace,
            "pod_count": 0,
            "event_count": 0,
            "evidence": [f"Kubernetes connector error: {exc}"],
            "error": str(exc)
        }

    crashloops = [p.metadata.name for p in pods.items if p.status.phase != "Running"]
    if crashloops:
        evidence.append(f"{len(crashloops)} pod(s) not running: {', '.join(crashloops[:3])}")
    else:
        evidence.append("All observed pods are running normally.")

    recent_events = [e.message for e in events.items if e.last_timestamp and e.last_timestamp >= datetime.utcnow() - timedelta(hours=2)]
    if recent_events:
        evidence.append(f"Recent events observed: {len(recent_events)}")

    pod_logs = []
    for pod in pods.items[:2]:
        try:
            log = v1.read_namespaced_pod_log(name=pod.metadata.name, namespace=namespace, tail_lines=20)
            if "error" in log.lower() or "exception" in log.lower():
                pod_logs.append(pod.metadata.name)
        except ApiException:
            continue

    if pod_logs:
        evidence.append(f"Error patterns found in pod logs: {', '.join(pod_logs)}")

    return {
        "namespace": namespace,
        "pod_count": len(pods.items),
        "event_count": len(events.items),
        "evidence": evidence
    }
