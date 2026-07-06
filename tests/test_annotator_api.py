# pyright: reportMissingImports=false
"""FastAPI annotator backend (needs the [annotator] extra; skipped if absent)."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from topofield.annotator.app import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_example_loads_valid_hdg():
    r = client.get("/api/example").json()
    assert "hdg" in r and r["stats"]["num_nodes"] == 10
    assert r["navigational_completeness"] == 1.0


def test_op_applies_and_returns_summary():
    ex = client.get("/api/example").json()["hdg"]
    r = client.post(
        "/api/op",
        json={
            "hdg": ex,
            "name": "set_function_label",
            "kwargs": {"zone_id": "icu_wing", "function_label": "ICU-2"},
        },
    )
    assert r.status_code == 200
    labels = {n["attrs"].get("function_label") for n in r.json()["hdg"]["nodes"]}
    assert "ICU-2" in labels


def test_invalid_op_returns_400():
    ex = client.get("/api/example").json()["hdg"]
    r = client.post(
        "/api/op",
        json={
            "hdg": ex,
            "name": "set_edge_type",
            "kwargs": {"u": "nurse", "v": "records", "tau": "teleporter"},
        },
    )
    assert r.status_code == 400


def test_extract_endpoint_builds_hdg():
    tess = {
        "nodes": [
            {"id": "room_1", "type": "room", "position": [0, 0]},
            {"id": "corridor_1", "type": "corridor", "position": [5, 5]},
        ],
        "edges": [{"source": "room_1", "target": "corridor_1"}],
    }
    r = client.post("/api/extract", json={"tesseract": tess, "building_id": "t"})
    assert r.status_code == 200 and r.json()["hdg"]["version"] == "0.1"


def test_validate_endpoint():
    ex = client.get("/api/example").json()["hdg"]
    assert client.post("/api/validate", json={"hdg": ex}).json()["ok"] is True
