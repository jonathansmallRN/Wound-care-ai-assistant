"""
Item 8 — Confidence score transparency.

Verifies area_signal_score, tissue_signal_score, drainage_signal_score are
returned by the classify endpoint, and that the confidence formula
  confidence = area × 0.50 + tissue × 0.30 + drainage × 0.20
matches the returned confidence_score.

Low-confidence test case (0.37):
  Baseline  4×4×1 cm  → area 16.00 cm²
  Follow-up 3.8×3.8×1 → area 14.44 cm²
  area_delta_pct = (16.00 - 14.44) / 16.00 × 100 = 9.75% → rounded to 9.8
  classification = STABLE  (9.8 ≤ 10)
  area_signal    = 1.0 - min(9.8/10.0, 1.0) = 0.02
  tissue_change  = improved (epithelial) → tissue_signal = 0.80
  drainage_change = stable  (minimal/serous, deterministic) → drainage_signal = 0.60
  confidence     = 0.02×0.50 + 0.80×0.30 + 0.60×0.20 = 0.010+0.240+0.120 = 0.37
"""
import pytest
from tests.conftest import make_assessment, make_case, run_full_pipeline


class TestConfidenceFormula:
    def test_signal_scores_returned_in_classify_response(self, client, db):
        """Classify endpoint returns the three signal scores."""
        case_id = make_case(client, "CONF-SIGNALS")
        make_assessment(client, case_id, date="2025-01-01")
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=3.8, width=3.8)
        fid = follow["assessment_id"]

        r = client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        assert r.status_code == 200
        r = client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})
        assert r.status_code == 200
        r = client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": fid})
        assert r.status_code == 200
        data = r.json()["data"]

        assert "area_signal_score" in data
        assert "tissue_signal_score" in data
        assert "drainage_signal_score" in data

    def test_confidence_formula_matches_components(self, client, db):
        """confidence_score == area×0.50 + tissue×0.30 + drainage×0.20 (within float rounding)."""
        case_id = make_case(client, "CONF-FORMULA")
        make_assessment(client, case_id, date="2025-01-01")
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=3.8, width=3.8)
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})
        r = client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": fid})
        data = r.json()["data"]

        expected = round(
            data["area_signal_score"] * 0.50
            + data["tissue_signal_score"] * 0.30
            + data["drainage_signal_score"] * 0.20,
            2,
        )
        assert data["confidence_score"] == expected, (
            f"confidence {data['confidence_score']} ≠ formula result {expected}"
        )

    def test_low_confidence_037_case(self, client, db):
        """Reproduce the 0.37 low-confidence reference case exactly.

        Baseline 4×4×1 cm → follow-up 3.8×3.8×1 cm with epithelial tissue and
        minimal serous drainage produces confidence_score=0.37, tier=low.
        """
        case_id = make_case(client, "CONF-LOW-037")
        make_assessment(client, case_id, date="2025-01-01",
                        length=4.0, width=4.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=3.8, width=3.8, depth=1.0,
                                  tissue_type="epithelial",
                                  drainage_amount="minimal",
                                  drainage_type="serous")
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})
        r = client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": fid})
        assert r.status_code == 200
        data = r.json()["data"]

        assert data["classification"] == "stable"
        assert data["confidence_score"] == 0.37
        assert data["confidence_tier"] == "low"
        assert data["area_signal_score"] == 0.02
        assert data["tissue_signal_score"] == 0.8
        assert data["drainage_signal_score"] == 0.6

    def test_improving_case_high_confidence(self, client, db):
        """Area > 10% reduction with improved tissue → improving, high confidence."""
        case_id = make_case(client, "CONF-HIGH")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        # 4×4 = 16 cm² from 25 cm² = 36% reduction → IMPROVING
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0,
                                  tissue_type="granulation",
                                  drainage_amount="minimal",
                                  drainage_type="serous")
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})
        r = client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": fid})
        assert r.status_code == 200
        data = r.json()["data"]

        assert data["classification"] == "improving"
        assert data["confidence_score"] >= 0.60

    def test_stable_boundary_at_exactly_10pct(self, client, db):
        """area_delta_pct = 10.0 → STABLE (spec says > 10 for improving, strict inequality)."""
        case_id = make_case(client, "CONF-BOUNDARY")
        # Baseline: 10 cm², follow-up: 9 cm²  → delta = 10.0%
        make_assessment(client, case_id, date="2025-01-01",
                        length=3.162, width=3.162, depth=1.0)   # ~10 cm²
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=3.0, width=3.0, depth=1.0,  # 9 cm²
                                  tissue_type="granulation",
                                  drainage_amount="minimal",
                                  drainage_type="serous")
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        r_long = client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})
        delta = r_long.json()["data"]["area_delta_pct"]
        r = client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": fid})
        data = r.json()["data"]

        # If delta rounds to exactly 10.0, classification must be stable.
        if delta == 10.0:
            assert data["classification"] == "stable", (
                f"delta={delta}%, expected stable but got {data['classification']}"
            )
