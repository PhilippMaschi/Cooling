import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from APP.backend.server import app  # noqa: E402

client = TestClient(app)
REQUEST_TIMEOUT = 10


@pytest.fixture(scope="module")
def project_id() -> str:
    return "AUT_2020_cooling"


def test_projects_endpoint_lists_expected_project(project_id: str):
    resp = client.get("/api/projects", timeout=REQUEST_TIMEOUT)
    assert resp.status_code == 200
    payload = resp.json()
    ids = {item["id"] for item in payload}
    assert project_id in ids


def test_project_scenarios_exposes_peaks(project_id: str):
    resp = client.get(f"/api/projects/{project_id}/scenarios", timeout=REQUEST_TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == project_id
    assert len(body["scenarios"]) >= 1

    first = body["scenarios"][0]
    assert first["total_cooling_load"] is not None
    assert first["peak_electric_load"] is not None


def test_timeseries_endpoint_returns_hourly_values(project_id: str):
    resp = client.get(
        f"/api/projects/{project_id}/scenarios/1/timeseries",
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scenario_id"] == 1
    assert body["aggregation"] == "hourly"
    assert len(body["values"]) == 8760
