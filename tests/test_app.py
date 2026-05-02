import json
import pytest

from app.main import app
import app.models as models
import app.metrics as metrics


@pytest.fixture(autouse=True)
def reset_store():
    models._notes.clear()
    models._next_id = 1
    # reset metrics counters so tests are independent
    metrics._total_requests = 0
    metrics._requests_by_method.clear()
    metrics._requests_by_status.clear()
    metrics._notes_created_total = 0
    metrics._notes_deleted_total = 0
    metrics._response_time_sum = 0.0
    metrics._response_time_count = 0
    metrics._activity_log.clear()
    yield
    models._notes.clear()
    models._next_id = 1


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Original tests ────────────────────────────────────────────────────────────
def test_index_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200


def test_health_returns_healthy(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_create_note(client):
    res = client.post(
        "/api/notes",
        data=json.dumps({"title": "Test", "content": "Hello"}),
        content_type="application/json",
    )
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["title"] == "Test"
    assert data["content"] == "Hello"
    assert "id" in data


def test_create_note_missing_title(client):
    res = client.post(
        "/api/notes",
        data=json.dumps({"content": "no title"}),
        content_type="application/json",
    )
    assert res.status_code == 400


def test_get_all_notes(client):
    client.post("/api/notes", data=json.dumps({"title": "A", "content": ""}), content_type="application/json")
    client.post("/api/notes", data=json.dumps({"title": "B", "content": ""}), content_type="application/json")
    res = client.get("/api/notes")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data) == 2


def test_delete_note(client):
    create_res = client.post(
        "/api/notes",
        data=json.dumps({"title": "To delete", "content": "bye"}),
        content_type="application/json",
    )
    note_id = json.loads(create_res.data)["id"]

    del_res = client.delete(f"/api/notes/{note_id}")
    assert del_res.status_code == 200

    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 404


# ── New tests ─────────────────────────────────────────────────────────────────
def test_metrics_endpoint_returns_valid_json(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    data = json.loads(res.data)
    expected_keys = {
        "total_requests", "requests_by_method", "requests_by_status",
        "notes_created_total", "notes_deleted_total",
        "average_response_time_ms", "uptime_seconds", "current_note_count",
        "activity_log",
    }
    assert expected_keys.issubset(data.keys())


def test_health_returns_all_expected_fields(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime_seconds" in data
    assert "checks" in data
    assert "memory_usage_mb" in data["checks"]
    assert "note_count" in data["checks"]
    assert "total_requests_served" in data["checks"]
    assert "environment" in data
    assert "python_version" in data["environment"]
    assert "container" in data["environment"]
    assert "azure" in data["environment"]


def test_dashboard_returns_200(client):
    res = client.get("/dashboard")
    assert res.status_code == 200


def test_create_note_increments_metrics_counter(client):
    before = metrics._notes_created_total
    client.post(
        "/api/notes",
        data=json.dumps({"title": "Metric test", "content": ""}),
        content_type="application/json",
    )
    assert metrics._notes_created_total == before + 1


def test_x_request_id_header_present(client):
    for path in ["/", "/health", "/api/notes", "/metrics", "/dashboard"]:
        res = client.get(path)
        assert "X-Request-ID" in res.headers, f"Missing X-Request-ID on {path}"
