import json
from typing import Any, Dict, List

import requests

from app.config import settings

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None


LOCAL_PROVIDER_ALIASES = {"local", "local_llm", "local-openai"}


def _create_openai_client() -> None:
    if openai is None:
        raise RuntimeError("OpenAI client is not installed")
    openai.api_key = settings.openai_api_key
    openai.timeout = settings.openai_timeout


def _extract_llm_content(response_data: Any) -> str:
    if isinstance(response_data, str):
        return response_data.strip()

    if not isinstance(response_data, dict):
        return json.dumps(response_data, indent=2)

    choices = response_data.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0]
        if isinstance(choice, dict):
            message = choice.get("message")
            if isinstance(message, dict):
                return message.get("content", "").strip()
            if isinstance(choice.get("text"), str):
                return choice.get("text", "").strip()

    for key in ("text", "response", "output", "message"):
        value = response_data.get(key)
        if isinstance(value, str):
            return value.strip()

    return json.dumps(response_data, indent=2)


def _call_openai(messages: List[Dict[str, str]]) -> str:
    if not settings.openai_api_key or settings.openai_api_key == "sk-test":
        raise ValueError("OPENAI_API_KEY is required for OpenAI LLM provider")

    _create_openai_client()

    response = openai.ChatCompletion.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
        request_timeout=settings.openai_timeout,
    )

    choice = response.choices[0]
    message = getattr(choice, "message", None)
    if message is None and isinstance(choice, dict):
        message = choice.get("message")

    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "") if message is not None else ""

    return content.strip() if isinstance(content, str) else str(content)


def _call_local_llm(messages: List[Dict[str, str]]) -> str:
    if not settings.local_llm_url:
        raise ValueError("LOCAL_LLM_URL is required for local LLM provider")

    payload = {
        "model": settings.local_llm_model,
        "messages": messages,
        "temperature": settings.openai_temperature,
        "max_tokens": settings.openai_max_tokens,
    }
    response = requests.post(settings.local_llm_url, json=payload, timeout=settings.openai_timeout)
    response.raise_for_status()

    try:
        response_data = response.json()
    except ValueError:
        return response.text.strip()

    return _extract_llm_content(response_data)


def _execute_llm(messages: List[Dict[str, str]]) -> str:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return _call_openai(messages)
    if provider in LOCAL_PROVIDER_ALIASES:
        return _call_local_llm(messages)

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def _prepare_review_messages(incident: Dict[str, Any], aggregate: Dict[str, Any]) -> List[Dict[str, str]]:
    evidence_list = aggregate.get("evidence", [])
    summaries = aggregate.get("agent_summaries", [])

    return [
        {
            "role": "system",
            "content": (
                "You are an incident response reasoning assistant. "
                "Analyze the incident context, evidence summary, and agent summaries to identify the likely root cause, confidence, and recommendation. "
                "Respond in valid JSON with keys: findings, confidence, root_cause, recommendation, reasoning."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "incident": {
                        "title": incident.get("title"),
                        "description": incident.get("description"),
                        "environment": incident.get("environment"),
                        "severity": incident.get("severity"),
                        "affected_service": incident.get("affected_service"),
                    },
                    "evidence": evidence_list,
                    "agent_summaries": summaries,
                },
                indent=2,
            ),
        },
    ]


def _prepare_report_messages(incident: Dict[str, Any], aggregate: Dict[str, Any], review: Dict[str, Any]) -> List[Dict[str, str]]:
    evidence_list = aggregate.get("evidence", [])
    summaries = aggregate.get("agent_summaries", [])

    return [
        {
            "role": "system",
            "content": (
                "You are an incident report generation assistant. "
                "Create a concise report summary, a recommendation, and a confidence estimate based on the incident context, evidence list, agent summaries, and review output. "
                "Respond in valid JSON with keys: summary, recommendation, confidence_estimates, reasoning."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "incident": {
                        "title": incident.get("title"),
                        "description": incident.get("description"),
                        "environment": incident.get("environment"),
                        "severity": incident.get("severity"),
                        "affected_service": incident.get("affected_service"),
                    },
                    "review": review,
                    "evidence": evidence_list,
                    "agent_summaries": summaries,
                },
                indent=2,
            ),
        },
    ]


def _parse_json_response(content: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = fallback.copy()
        parsed.update({"reasoning": content})
        return parsed

    if "confidence" in parsed and isinstance(parsed["confidence"], str):
        try:
            parsed["confidence"] = float(parsed["confidence"])
        except ValueError:
            parsed["confidence"] = 0.0

    return parsed


def generate_incident_review(incident: Dict[str, Any], aggregate: Dict[str, Any]) -> Dict[str, Any]:
    if settings.llm_provider.lower() == "openai" and (not settings.openai_api_key or settings.openai_api_key == "sk-test"):
        return {
            "findings": "Incident review fallback: unable to reach OpenAI.",
            "confidence": 0.0,
            "root_cause": "LLM reasoning unavailable",
            "recommendation": "Provide a valid OPENAI_API_KEY or configure a response stub.",
            "reasoning": "OpenAI API key is missing or using the placeholder default.",
        }

    messages = _prepare_review_messages(incident, aggregate)

    try:
        content = _execute_llm(messages)
    except Exception as exc:
        content = str(exc)

    fallback = {
        "findings": content,
        "confidence": 0.0,
        "root_cause": "Could not parse LLM response",
        "recommendation": "Inspect LLM output for details.",
        "reasoning": content,
    }
    parsed = _parse_json_response(content, fallback)

    return parsed


def generate_incident_report(incident: Dict[str, Any], aggregate: Dict[str, Any], review: Dict[str, Any]) -> Dict[str, Any]:
    if settings.llm_provider.lower() == "openai" and (not settings.openai_api_key or settings.openai_api_key == "sk-test"):
        return {
            "summary": "Incident report fallback: unable to reach OpenAI.",
            "recommendation": "Provide a valid OPENAI_API_KEY or configure a response stub.",
            "confidence_estimates": {"overall": 0.0},
            "reasoning": "OpenAI API key is missing or using the placeholder default.",
        }

    messages = _prepare_report_messages(incident, aggregate, review)

    try:
        content = _execute_llm(messages)
    except Exception as exc:
        content = str(exc)

    fallback = {
        "summary": content,
        "recommendation": "Inspect LLM output for details.",
        "confidence_estimates": {"overall": 0.0},
        "reasoning": content,
    }
    parsed = _parse_json_response(content, fallback)

    if "confidence_estimates" not in parsed and "confidence" in parsed:
        try:
            parsed["confidence_estimates"] = {"overall": float(parsed.get("confidence", 0.0))}
        except ValueError:
            parsed["confidence_estimates"] = {"overall": 0.0}

    return parsed
