"""Test API endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_health_check():
    """Health check endpoint test."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_create_incident():
    """Incident creation endpoint test."""
    payload = {
        "title": "High CPU usage",
        "description": "Service pods showing 95% CPU usage for last 10 minutes",
        "environment": "prod",
        "severity": "high",
        "affected_service": "payment-service"
    }

    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["environment"] == "prod"
    assert data["severity"] == "high"
    assert data["status"] == "resolved"
    assert "id" in data


def test_list_incidents():
    """List incidents endpoint test."""
    response = client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_incident_not_found():
    """Get missing incident test."""
    response = client.get("/api/incidents/inc_nonexistent")
    assert response.status_code == 404


def test_invalid_incident_create():
    """Invalid incident creation test."""
    payload = {
        "title": "",
        "description": "Too short",
        "environment": "prod",
        "severity": "high"
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 422
