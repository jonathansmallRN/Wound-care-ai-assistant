"""
Tests for image upload security — path traversal (item 1) and
duplicate-filename overwrite (item 2).
"""
import io
import pathlib

from starlette.testclient import TestClient

from tests.conftest import make_assessment, make_case

_TINY_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1eB"
    b"\xed\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14"
    b"\xff\xd9"
)


def _upload(client: TestClient, assessment_id: str, *, filename: str) -> dict:
    r = client.post(
        "/api/v1/images",
        data={"assessment_id": assessment_id},
        files={"image_file": (filename, io.BytesIO(_TINY_JPEG), "image/jpeg")},
    )
    return r


# ── Item 1: Path traversal ────────────────────────────────────────────────────

class TestPathTraversal:
    def _setup(self, client, db):
        case_id = make_case(client, "IMG-TRAVERSAL")
        make_assessment(client, case_id, date="2025-01-01")
        follow = make_assessment(client, case_id, date="2025-01-08")
        return follow["assessment_id"]

    def test_unix_traversal_filename_blocked(self, client, db, tmp_path):
        """../../../etc/passwd must not escape the upload directory."""
        aid = self._setup(client, db)
        import os
        media_root = os.environ["MEDIA_ROOT"]

        r = _upload(client, aid, filename="../../../etc/passwd")
        assert r.status_code == 200, r.text

        # The stored filename must be within assessment_dir, not outside media_root.
        storage_name = r.json()["data"]["filename"]
        expected_dir = pathlib.Path(media_root) / aid
        stored_path = expected_dir / storage_name

        # File must exist inside the assessment directory.
        assert stored_path.exists(), f"file not found at {stored_path}"
        # The storage name must not start with .. or contain a path separator.
        assert ".." not in storage_name
        assert "/" not in storage_name
        assert "\\" not in storage_name

    def test_windows_traversal_filename_blocked(self, client, db):
        """..\\..\\evil.jpg must not escape the upload directory."""
        aid = self._setup(client, db)
        import os
        media_root = os.environ["MEDIA_ROOT"]

        r = _upload(client, aid, filename="..\\..\\evil.jpg")
        assert r.status_code == 200, r.text

        storage_name = r.json()["data"]["filename"]
        expected_dir = pathlib.Path(media_root) / aid
        stored_path = expected_dir / storage_name

        assert stored_path.exists(), f"file not found at {stored_path}"
        assert ".." not in storage_name
        assert "/" not in storage_name
        assert "\\" not in storage_name

    def test_absolute_path_filename_blocked(self, client, db):
        """/etc/shadow as filename must not write outside upload dir."""
        aid = self._setup(client, db)
        import os
        media_root = os.environ["MEDIA_ROOT"]

        r = _upload(client, aid, filename="/etc/shadow")
        assert r.status_code == 200, r.text

        storage_name = r.json()["data"]["filename"]
        stored_path = pathlib.Path(media_root) / aid / storage_name
        assert stored_path.exists()
        assert "/" not in storage_name.lstrip("/")  # no dir separator after UUID

    def test_null_byte_filename_safe(self, client, db):
        """Null byte in filename must not cause issues."""
        aid = self._setup(client, db)
        r = _upload(client, aid, filename="evil\x00.jpg")
        assert r.status_code == 200, r.text
        storage_name = r.json()["data"]["filename"]
        assert "\x00" not in storage_name

    def test_storage_url_within_media_base(self, client, db):
        """storage_url must start with the configured media base URL."""
        import os
        aid = self._setup(client, db)
        r = _upload(client, aid, filename="../escape.jpg")
        assert r.status_code == 200, r.text
        storage_url = r.json()["data"]["storage_url"]
        assert storage_url.startswith(os.environ["MEDIA_BASE_URL"])


# ── Item 2: Duplicate filename overwrite ──────────────────────────────────────

class TestDuplicateFilename:
    def _setup(self, client, db):
        case_id = make_case(client, "IMG-DUP")
        make_assessment(client, case_id, date="2025-01-01")
        follow = make_assessment(client, case_id, date="2025-01-08")
        return follow["assessment_id"]

    def test_same_original_name_creates_separate_files(self, client, db):
        """Two uploads with the same original filename produce distinct stored files."""
        import os
        aid = self._setup(client, db)
        media_root = os.environ["MEDIA_ROOT"]

        r1 = _upload(client, aid, filename="wound.jpg")
        r2 = _upload(client, aid, filename="wound.jpg")

        assert r1.status_code == 200, r1.text
        assert r2.status_code == 200, r2.text

        name1 = r1.json()["data"]["filename"]
        name2 = r2.json()["data"]["filename"]

        # Storage keys must differ.
        assert name1 != name2, "Two uploads with identical filenames must not share a storage key"

        # Both files must exist on disk.
        base = pathlib.Path(media_root) / aid
        assert (base / name1).exists(), f"First upload not found: {base / name1}"
        assert (base / name2).exists(), f"Second upload not found: {base / name2}"

    def test_sequential_images_both_retrievable(self, client, db):
        """Each upload creates an independent Image record and file."""
        import os
        aid = self._setup(client, db)
        media_root = os.environ["MEDIA_ROOT"]

        r1 = _upload(client, aid, filename="photo.png")
        r2 = _upload(client, aid, filename="photo.png")

        id1 = r1.json()["data"]["image_id"]
        id2 = r2.json()["data"]["image_id"]
        assert id1 != id2, "Each upload must produce a distinct image record"
