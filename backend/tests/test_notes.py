"""
Item 4 — Editable progress note persistence.

Tests for PATCH /api/v1/assessments/{id}/note:
- Clinician edits are saved to the database.
- Editing before note generation returns an error.
- Baseline assessments cannot be edited.
"""
from tests.conftest import make_assessment, make_case, run_full_pipeline


def _complete_workflow(client, db) -> str:
    """Create a case, run the full pipeline through review, generate a note."""
    case_id = make_case(client, "NOTE-TEST")
    make_assessment(client, case_id, date="2025-01-01",
                    length=5.0, width=5.0, depth=1.0)
    follow = make_assessment(client, case_id, date="2025-01-08",
                              length=4.0, width=4.0, depth=1.0,
                              tissue_type="granulation",
                              drainage_amount="none",
                              drainage_type="serous")
    fid = follow["assessment_id"]
    classify = run_full_pipeline(client, fid)

    r = client.post("/api/v1/review", json={
        "assessment_id": fid,
        "review_status": "overridden",
        "clinician_classification": classify["classification"],
        "override_reason": "Workflow test",
        "fitzpatrick_scale": "II",
    })
    assert r.status_code == 200, r.text

    r = client.post("/api/v1/notes/generate", json={"assessment_id": fid})
    assert r.status_code == 200, r.text
    return fid


class TestNoteEditable:
    def test_patch_saves_edit(self, client, db):
        """PATCH /assessments/{id}/note persists the edited text."""
        fid = _complete_workflow(client, db)
        edited = "CLINICIAN EDIT: Updated note for test."

        r = client.patch(f"/api/v1/assessments/{fid}/note", json={"note_draft": edited})
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["note_draft"] == edited
        assert data["note_id"] == fid

    def test_patch_idempotent_on_repeated_save(self, client, db):
        """Multiple PATCHes update the note each time."""
        fid = _complete_workflow(client, db)

        client.patch(f"/api/v1/assessments/{fid}/note", json={"note_draft": "First edit"})
        r = client.patch(f"/api/v1/assessments/{fid}/note", json={"note_draft": "Second edit"})

        assert r.status_code == 200
        assert r.json()["data"]["note_draft"] == "Second edit"

    def test_patch_before_generation_fails(self, client, db):
        """PATCH before note is generated returns an error (note_draft is null)."""
        case_id = make_case(client, "NOTE-NOTENYET")
        make_assessment(client, case_id, date="2025-01-01",
                        length=5.0, width=5.0, depth=1.0)
        follow = make_assessment(client, case_id, date="2025-01-08",
                                  length=4.0, width=4.0, depth=1.0)
        fid = follow["assessment_id"]

        r = client.patch(f"/api/v1/assessments/{fid}/note", json={"note_draft": "premature"})
        assert r.status_code == 422
        assert r.json()["success"] is False

    def test_patch_baseline_fails(self, client, db):
        """Baseline assessments cannot be edited via PATCH note."""
        case_id = make_case(client, "NOTE-BASELINE")
        baseline = make_assessment(client, case_id, date="2025-01-01",
                                    length=4.0, width=4.0, depth=1.0)
        bid = baseline["assessment_id"]
        assert baseline["is_baseline"] is True

        r = client.patch(f"/api/v1/assessments/{bid}/note", json={"note_draft": "edit"})
        assert r.status_code == 422
        assert r.json()["success"] is False
