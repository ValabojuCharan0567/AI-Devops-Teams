"""Tests for LLM tool provider selection."""

import json
from unittest.mock import patch

import pytest

from tools import llm_tools
from app.config import settings


def test_execute_llm_uses_openai_by_default(monkeypatch):
    settings.llm_provider = "openai"
    settings.openai_api_key = "sk-valid"

    with patch("tools.llm_tools._call_openai", return_value="{\"findings\": \"OK\", \"confidence\": 0.5, \"root_cause\": \"test\", \"recommendation\": \"fix\", \"reasoning\": \"done\"}") as mock_openai:
        result = llm_tools.generate_incident_review({"title": "t"}, {})
        assert mock_openai.called
        assert result["findings"] == "OK"


def test_execute_llm_uses_local_provider(monkeypatch):
    settings.llm_provider = "local"
    settings.local_llm_url = "http://127.0.0.1:8000/v1/chat/completions"

    with patch("tools.llm_tools._call_local_llm", return_value="{\"summary\": \"OK\", \"recommendation\": \"fix\", \"confidence_estimates\": {\"overall\": 0.8}, \"reasoning\": \"done\"}") as mock_local:
        result = llm_tools.generate_incident_report({"title": "t"}, {}, {"findings": "ok"})
        assert mock_local.called
        assert result["summary"] == "OK"


def test_unsupported_provider_raises(monkeypatch):
    settings.llm_provider = "unknown"
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        llm_tools._execute_llm([])
