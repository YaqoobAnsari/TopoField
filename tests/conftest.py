import copy
import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "hospital_toy.json"


@pytest.fixture
def toy_path() -> Path:
    return FIXTURE


@pytest.fixture
def toy_graph() -> dict:
    """A fresh deep copy of the canonical hospital toy graph per test."""
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))
