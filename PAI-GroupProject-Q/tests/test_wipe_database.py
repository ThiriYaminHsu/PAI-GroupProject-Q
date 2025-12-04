"""Tests for `WipeDatabase.py`.

These tests run the script as a separate process with `cwd` set to a temporary
folder so the script's relative `DB_FILE = Path("student_wellbeing_db.sqlite3")`
operates on an isolated file created within the temp dir.
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


def _get_script_path():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "src" / "Student_Wellbeing_App" / "core" / "database" / "WipeDatabase.py"


def test_wipe_database_when_file_missing(tmp_path):
    """When DB file is absent, script prints a warning and does nothing."""
    script = _get_script_path()

    # Ensure no DB file in the tmp cwd
    assert not (tmp_path / "student_wellbeing_db.sqlite3").exists()

    proc = subprocess.run([sys.executable, str(script)], cwd=str(
        tmp_path), capture_output=True, text=True)

    out = proc.stdout + proc.stderr
    assert "Database file not found" in out
    assert not (tmp_path / "student_wellbeing_db.sqlite3").exists()


def test_wipe_database_deletes_file(tmp_path):
    """When DB file exists, script should delete it and print success message."""
    script = _get_script_path()
    db_file = tmp_path / "student_wellbeing_db.sqlite3"

    # Create SQLite DB file in the temporary directory
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE demo(id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    assert db_file.exists()

    proc = subprocess.run([sys.executable, str(script)], cwd=str(
        tmp_path), capture_output=True, text=True)

    out = proc.stdout + proc.stderr
    assert "SQLite database file deleted" in out
    assert not db_file.exists()
