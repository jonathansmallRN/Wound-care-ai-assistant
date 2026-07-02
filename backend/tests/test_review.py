"""
Item 3 — fitzpatrick_scale required at backend/service layer.

The review endpoint must reject submissions that omit fitzpatrick_scale,
regardless of whether review_status is 'accepted' or 'overridden'.
"""
from tests.conftest import make_assessment, make_case, run_full_pipeline


def _setup_reviewed_pipeline(client, db):
    """Return an assessment_id that has completed vision→classify→explainability."""
    case_id = make_case(client, "FITZ-TEST")
    make_assessment(client, case_id, date="2025-01-01",
                    length=5.0, width=5.0, depth=1.0)
    follow = make_assessment(client, case_id, date="2025-01-08",
                              length=5.0, width=5.0, depth=1.0)
    fid = follow["assessment_id"]
    run_full_pipeline(client, fid)
    return fid


class TestFitzpatrickRequired:
    def test_accept_without_fitzpatrick_rejected(self, client, db):
        """Accepting without fitzpatrick_scale returns VALIDATION_ERROR."""
        fid = _setup_reviewed_pipeline(client, db)

        r = client.post("/api/v1/review", json={
            "assessment_id": fid,
            "review_status": "accepted",
            # no fitzpatrick_scale
        })
        assert r.status_code == 422
        body = r.json()
        assert body["success"] is False
        assert body["error_code"] == "VALIDATION_ERROR"
        assert "fitzpatrick_scale" in body["message"]

    def test_override_without_fitzpatrick_rejected(self, client, db):
        """Overriding without fitzpatrick_scale returns VALIDATION_ERROR."""
        fid = _setup_reviewed_pipeline(client, db)

        r = client.post("/api/v1/review", json={
            "assessment_id": fid,
            "review_status": "overridden",
            "clinician_classification": "stable",
            "override_reason": "Manual review",
            # no fitzpatrick_scale
        })
        assert r.status_code == 422
        body = r.json()
        assert body["success"] is False
        assert body["error_code"] == "VALIDATION_ERROR"

    def test_accept_with_fitzpatrick_succeeds(self, client, db):
        """Accepting with fitzpatrick_scale succeeds (medium/high confidence case)."""
        case_id = make_case(client, "FITZ-ACCEPT")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        # Big improvement → high confidence
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0,
                                  tissue_type="granulation",
                                  drainage_amount="none",
                                  drainage_type="serous")
        fid = follow["assessment_id"]
        classify = run_full_pipeline(client, fid)

        if classify["confidence_tier"] in ("high", "medium"):
            r = client.post("/api/v1/review", json={
                "assessment_id": fid,
                "review_status": "accepted",
                "fitzpatrick_scale": "III",
            })
            assert r.status_code == 200
            assert r.json()["success"] is True

    def test_override_with_fitzpatrick_succeeds(self, client, db):
        """Overriding with fitzpatrick_scale and valid fields succeeds."""
        fid = _setup_reviewed_pipeline(client, db)

        r = client.post("/api/v1/review", json={
            "assessment_id": fid,
            "review_status": "overridden",
            "clinician_classification": "stable",
            "override_reason": "Clinician disagrees with AI result",
            "fitzpatrick_scale": "IV",
        })
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_fitzpatrick_null_explicit_rejected(self, client, db):
        """Explicitly passing null fitzpatrick_scale is rejected."""
        fid = _setup_reviewed_pipeline(client, db)

        r = client.post("/api/v1/review", json={
            "assessment_id": fid,
            "review_status": "overridden",
            "clinician_classification": "stable",
            "override_reason": "Test",
            "fitzpatrick_scale": None,
        })
        assert r.status_code == 422
        assert r.json()["success"] is False
