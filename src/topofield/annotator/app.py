"""FastAPI backend for the HDG annotator.

Stateless transform service: the browser holds the HDG and posts it with an
operation; the server applies the (validated) engine operation and returns the new
HDG + summary. The server therefore can NEVER return an invalid graph. No routing /
navigation endpoints (deliberately removed — this tool builds HDGs, it does not
route). Requires the [annotator] extra: `pip install -e .[annotator]`.

Run: `uvicorn topofield.annotator.app:app --host 0.0.0.0 --port 8000`
(on a Slurm interactive node; forward the port to view the UI).
"""

# pyright: reportMissingImports=false
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..extraction.tesseract_adapter import tesseract_json_to_hdg
from ..graph import HDG, validate
from ..metrics import navigational_completeness
from . import operations as ops

_STATIC = Path(__file__).parent / "static"
_FIXTURE = Path(__file__).parents[3] / "tests" / "fixtures" / "hospital_toy.json"

app = FastAPI(title="TopoField — HDG Annotator", version="0.1.0")


class OpRequest(BaseModel):
    hdg: dict[str, Any]
    name: str
    kwargs: dict[str, Any] = {}


class ExtractRequest(BaseModel):
    tesseract: dict[str, Any]
    building_id: str = "building"


class HDGRequest(BaseModel):
    hdg: dict[str, Any]


def _summary(hdg: dict[str, Any]) -> dict[str, Any]:
    h = HDG.from_dict(hdg)
    return {"stats": h.stats(), "navigational_completeness": round(navigational_completeness(h), 4)}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/example")
def example() -> dict[str, Any]:
    hdg = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return {"hdg": hdg, **_summary(hdg)}


@app.post("/api/extract")
def extract(req: ExtractRequest) -> dict[str, Any]:
    """Tesseract BuildingGraph JSON -> HDG scaffold (via the adapter)."""
    try:
        hdg = tesseract_json_to_hdg(req.tesseract, building_id=req.building_id)
    except Exception as exc:  # noqa: BLE001 - surface adapter errors to the client
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"hdg": hdg, **_summary(hdg)}


@app.post("/api/op")
def apply_op(req: OpRequest) -> dict[str, Any]:
    """Apply one annotation operation; returns the new (validated) HDG + summary."""
    try:
        hdg = ops.apply_operation(req.hdg, req.name, **req.kwargs)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"hdg": hdg, **_summary(hdg)}


@app.post("/api/validate")
def validate_ep(req: HDGRequest) -> dict[str, Any]:
    result = validate(req.hdg)
    return {"ok": result.ok, "errors": result.errors}


@app.get("/api/operations")
def list_operations() -> dict[str, list[str]]:
    return {"operations": sorted(ops.OPERATIONS)}


if _STATIC.exists():  # serve the SPA (mounted last so /api/* wins)
    app.mount("/", StaticFiles(directory=str(_STATIC), html=True), name="static")
