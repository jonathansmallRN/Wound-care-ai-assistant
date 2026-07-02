"""
Item 5 — Audit log completeness.

After running the full pipeline (vision → longitudinal → clinical_assessment →
explainability → notes), GET /audit/{assessment_id} must return entries for
all five service names.
"""
from tests.conftest import make_assessment, make_case, run_full_pipeline


class TestAuditCompleteness:
    def test_all_five_services_in_audit_log(self, client, db):
        """All five pipeline services generate audit log entries."""
        case_id = make_case(client, "AUDIT-FULL")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0,
                                  tissue_type="granulation",
                                  drainage_amount="none",
                                  drainage_type="serous")
        fid = follow["assessment_id"]

        # Run vision → longitudinal → classify → explainability
        run_full_pipeline(client, fid)

        # Complete review (required before note generation)
        r = client.post("/api/v1/review", json={
            "assessment_id": fid,
            "review_status": "overridden",
            "clinician_classification": "improving",
            "override_reason": "Audit test",
            "fitzpatrick_scale": "V",
        })
        assert r.status_code == 200, r.text

        # Generate note
        r = client.post("/api/v1/notes/generate", json={"assessment_id": fid})
        assert r.status_code == 200, r.text

        # Check audit log
        r = client.get(f"/api/v1/audit/{fid}")
        assert r.status_code == 200, r.text
        entries = r.json()["data"]
        service_names = {e["service_name"] for e in entries}

        assert "vision" in service_names, f"vision missing from audit log: {service_names}"
        assert "longitudinal" in service_names, f"longitudinal missing: {service_names}"
        assert "clinical_assessment" in service_names, f"clinical_assessment missing: {service_names}"
        assert "explainability" in service_names, f"explainability missing: {service_names}"
        assert "notes" in service_names, f"notes missing from audit log: {service_names}"

    def test_audit_entries_have_required_fields(self, client, db):
        """Each audit log entry has service_name, success, and created_at."""
        case_id = make_case(client, "AUDIT-FIELDS")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0)
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})

        r = client.get(f"/api/v1/audit/{fid}")
        assert r.status_code == 200
        entries = r.json()["data"]
        assert len(entries) >= 1

        for entry in entries:
            assert "service_name" in entry, f"service_name missing in {entry}"
            assert "success" in entry, f"success missing in {entry}"
            assert "created_at" in entry, f"created_at missing in {entry}"

    def test_longitudinal_audit_entry_present(self, client, db):
        """Longitudinal service creates an audit log entry (was missing before fix)."""
        case_id = make_case(client, "AUDIT-LONG")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0)
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})

        r = client.get(f"/api/v1/audit/{fid}")
        service_names = {e["service_name"] for e in r.json()["data"]}
        assert "longitudinal" in service_names

    def test_clinical_assessment_audit_entry_present(self, client, db):
        """Clinical assessment service creates an audit log entry (was missing before fix)."""
        case_id = make_case(client, "AUDIT-CLASSIFY")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0)
        fid = follow["assessment_id"]

        client.post("/api/v1/vision/analyze", json={"assessment_id": fid})
        client.post("/api/v1/longitudinal/analyze", json={"assessment_id": fid})
        client.post("/api/v1/clinical-assessment/classify", json={"assessment_id": fid})

        r = client.get(f"/api/v1/audit/{fid}")
        service_names = {e["service_name"] for e in r.json()["data"]}
        assert "clinical_assessment" in service_names

    def test_all_audit_entries_successful(self, client, db):
        """All pipeline steps succeed (success=True) in mock mode."""
        case_id = make_case(client, "AUDIT-SUCCESS")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0,
                                  tissue_type="granulation",
                                  drainage_amount="none",
                                  drainage_type="serous")
        fid = follow["assessment_id"]
        run_full_pipeline(client, fid)

        client.post("/api/v1/review", json={
            "assessment_id": fid,
            "review_status": "overridden",
            "clinician_classification": "improving",
            "override_reason": "Audit success test",
            "fitzpatrick_scale": "I",
        })
        client.post("/api/v1/notes/generate", json={"assessment_id": fid})

        r = client.get(f"/api/v1/audit/{fid}")
        for entry in r.json()["data"]:
            assert entry["success"] is True, (
                f"service {entry['service_name']} reported failure in mock mode"
            )
