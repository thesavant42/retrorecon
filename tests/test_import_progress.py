import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def test_import_progress(tmp_path, monkeypatch):
    progress_file = tmp_path / "progress.json"
    monkeypatch.setattr(app, "IMPORT_PROGRESS_FILE", str(progress_file))

    # Ensure progress file starts absent
    assert not progress_file.exists()

    app.set_import_progress("running", "importing", 5, 10)
    data = app.get_import_progress()
    assert data == {"status": "running", "message": "importing", "current": 5, "total": 10}

    app.clear_import_progress()
    assert not progress_file.exists()


def test_get_progress_bad_json(tmp_path, monkeypatch):
    progress_file = tmp_path / "progress.json"
    progress_file.write_text("nonsense")
    monkeypatch.setattr(app, "IMPORT_PROGRESS_FILE", str(progress_file))

    data = app.get_import_progress()
    assert data == {"status": "idle", "message": "", "current": 0, "total": 0}
