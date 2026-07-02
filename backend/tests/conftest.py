"""Test fixtures.

Sets environment variables BEFORE importing any app modules so that
pydantic-settings picks up the test values (Settings is a module-level
singleton created at first import).
"""
import os
import pathlib

# Must be set before app is imported.
_TEST_MEDIA = "/tmp/wound_test_media"
pathlib.Path(_TEST_MEDIA).mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATABASE_URL", "postgresql://wound_care:wound_care@localhost:5432/wound_care")
os.environ["MOCK_AI_MODE"] = "true"
os.environ["MEDIA_ROOT"] = _TEST_MEDIA
os.environ["MEDIA_BASE_URL"] = "http://testserver/media"
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.database import get_db
from app.main import app

_engine = create_engine(os.environ["DATABASE_URL"])


@pytest.fixture()
def db():
    """Transaction-wrapped session — rolls back after each test."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient wired to the transaction-wrapped session."""
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── Shared helpers ────────────────────────────────────────────────────────────

def make_case(client: TestClient, ref: str = "TEST-CASE") -> str:
    r = client.post("/api/v1/cases", json={"case_ref": ref})
    assert r.status_code == 200, r.text
    return r.json()["data"]["id"]


def make_assessment(
    client: TestClient,
    case_id: str,
    *,
    date: str = "2025-01-01",
    length: float = 4.0,
    width: float = 4.0,
    depth: float = 1.0,
    tissue_type: str = "epithelial",
    drainage_amount: str = "minimal",
    drainage_type: str = "serous",
    periwound: str = "intact",
) -> dict:
    r = client.post("/api/v1/assessments", json={
        "case_id": case_id,
        "assessment_date": date,
        "length_cm": length,
        "width_cm": width,
        "depth_cm": depth,
        "tissue_type": tissue_type,
        "drainage_amount": drainage_amount,
        "drainage_type": drainage_type,
        "periwound": periwound,
    })
    assert r.status_code == 200, r.text
    return r.json()["data"]


def run_full_pipeline(client: TestClient, assessment_id: str) -> dict:
    """Run vision → longitudinal → classify → explainability and return classify data."""
    r = client.post("/api/v1/vision/analyze", json={"assessment_id": assessment_id})
    assert r.status_code == 200, f"vision: {r.text}"

    r = client.post("/api/v1/longitudinal/analyze", json={"assessment_id": assessment_id})
    assert r.status_code == 200, f"longitudinal: {r.text}"

    r = client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": assessment_id})
    assert r.status_code == 200, f"classify: {r.text}"
    classify = r.json()["data"]

    r = client.post("/api/v1/explainability/generate", json={"assessment_id": assessment_id})
    assert r.status_code == 200, f"explainability: {r.text}"

    return classify
