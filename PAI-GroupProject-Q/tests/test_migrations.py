import sqlite3
import pytest

from Student_Wellbeing_App.core.database import connection as db_conn
from Student_Wellbeing_App.core.database import migrations


def _use_temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "migrations.sqlite3"
    monkeypatch.setattr(db_conn, "DB_PATH", db_file)
    monkeypatch.setattr(db_conn, "DB_NAME", db_file)
    monkeypatch.setattr(migrations, "DB_NAME", db_file)
    return db_file


class TestRunMigrationsCreatesTables:
    """Test suite for table creation in run_migrations"""

    def test_run_migrations_creates_expected_tables(self, tmp_path, monkeypatch):
        """Verify all required tables are created"""
        _use_temp_db(tmp_path, monkeypatch)

        migrations.run_migrations()  # first run
        migrations.run_migrations()  # idempotent

        con = db_conn.get_db_connection()
        tables = {
            row["name"]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        expected = {
            "student",
            "attendance",
            "assessment",
            "submission",
            "wellbeing_record",
            "alert",
            "retention_rule",
            "audit_log",
            "user",
        }
        assert expected.issubset(tables)
        con.close()

    def test_run_migrations_idempotent(self, tmp_path, monkeypatch):
        """Verify migrations can be run multiple times safely"""
        _use_temp_db(tmp_path, monkeypatch)

        # Run twice
        migrations.run_migrations()
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        tables = {
            row["name"]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        # Should have all tables still
        assert len(tables) >= 9
        con.close()


class TestStudentTable:
    """Test suite for student table schema"""

    def test_student_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify student table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"]
                for row in con.execute("PRAGMA table_info(student)")}
        expected = {"student_id", "first_name",
                    "lastname", "email", "password", "year"}
        assert expected <= cols
        con.close()

    def test_student_id_is_primary_key(self, tmp_path, monkeypatch):
        """Verify student_id is the primary key"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        pk_info = con.execute("PRAGMA table_info(student)").fetchall()
        student_id_col = next(
            row for row in pk_info if row["name"] == "student_id")
        assert student_id_col["pk"] == 1  # pk=1 means it's the primary key
        con.close()

    def test_student_email_is_unique(self, tmp_path, monkeypatch):
        """Verify email column has unique constraint"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S001', 'John', 'Doe', 'john@example.com', 'pass123', 1)"
        )
        con.commit()

        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
                "VALUES ('S002', 'Jane', 'Smith', 'john@example.com', 'pass456', 1)"
            )
            con.commit()
        con.close()

    def test_student_insert_and_retrieve(self, tmp_path, monkeypatch):
        """Verify can insert and retrieve student records"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S001', 'John', 'Doe', 'john@example.com', 'pass123', 2)"
        )
        con.commit()

        row = con.execute(
            "SELECT * FROM student WHERE student_id = 'S001'").fetchone()
        assert row["first_name"] == "John"
        assert row["lastname"] == "Doe"
        assert row["year"] == 2
        con.close()


class TestAttendanceTable:
    """Test suite for attendance table schema"""

    def test_attendance_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify attendance table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"]
                for row in con.execute("PRAGMA table_info(attendance)")}
        expected = {
            "attendance_id",
            "student_id",
            "session_date",
            "session_id",
            "status",
        }
        assert expected <= cols
        con.close()

    def test_attendance_foreign_key_constraint(self, tmp_path, monkeypatch):
        """Verify attendance.student_id has FK to student.student_id"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        # Try to insert with invalid student_id
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO attendance(student_id, session_date, session_id, status) "
                "VALUES ('INVALID', '2025-01-01', 'S1', 'present')"
            )
            con.commit()
        con.close()

    def test_attendance_autoincrement_id(self, tmp_path, monkeypatch):
        """Verify attendance_id auto-increments"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        # Add a student first
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S001', 'John', 'Doe', 'john@example.com', 'pass', 1)"
        )
        con.commit()

        # Insert two attendance records
        con.execute(
            "INSERT INTO attendance(student_id, session_date, session_id, status) "
            "VALUES ('S001', '2025-01-01', 'sess1', 'present')"
        )
        con.execute(
            "INSERT INTO attendance(student_id, session_date, session_id, status) "
            "VALUES ('S001', '2025-01-02', 'sess2', 'absent')"
        )
        con.commit()

        rows = con.execute(
            "SELECT attendance_id FROM attendance ORDER BY attendance_id").fetchall()
        assert len(rows) == 2
        assert rows[0]["attendance_id"] == 1
        assert rows[1]["attendance_id"] == 2
        con.close()


class TestAssessmentTable:
    """Test suite for assessment table schema"""

    def test_assessment_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify assessment table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"]
                for row in con.execute("PRAGMA table_info(assessment)")}
        expected = {"assessment_id", "module_code",
                    "title", "due_date", "weight"}
        assert expected <= cols
        con.close()

    def test_assessment_insert_and_retrieve(self, tmp_path, monkeypatch):
        """Verify can insert and retrieve assessment records"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        con.execute(
            "INSERT INTO assessment(module_code, title, due_date, weight) "
            "VALUES ('CS101', 'Exam 1', '2025-05-01', 0.5)"
        )
        con.commit()

        row = con.execute(
            "SELECT * FROM assessment WHERE module_code = 'CS101'"
        ).fetchone()
        assert row["title"] == "Exam 1"
        assert row["weight"] == 0.5
        con.close()


class TestSubmissionTable:
    """Test suite for submission table schema"""

    def test_submission_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify submission table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"]
                for row in con.execute("PRAGMA table_info(submission)")}
        expected = {
            "submission_id",
            "student_id",
            "assessment_id",
            "submitted_at",
            "status",
            "mark",
        }
        assert expected <= cols
        con.close()

    def test_submission_foreign_key_student(self, tmp_path, monkeypatch):
        """Verify submission.student_id has FK to student"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO submission(student_id, assessment_id, submitted_at, status) "
                "VALUES ('INVALID', 1, datetime('now'), 'submitted')"
            )
            con.commit()
        con.close()

    def test_submission_foreign_key_assessment(self, tmp_path, monkeypatch):
        """Verify submission.assessment_id has FK to assessment"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        # Add a student
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S001', 'John', 'Doe', 'john@example.com', 'pass', 1)"
        )
        con.commit()

        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO submission(student_id, assessment_id, submitted_at, status) "
                "VALUES ('S001', 999, datetime('now'), 'submitted')"
            )
            con.commit()
        con.close()


class TestWellbeingRecordTable:
    """Test suite for wellbeing_record table schema"""

    def test_wellbeing_record_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify wellbeing_record table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"] for row in con.execute(
            "PRAGMA table_info(wellbeing_record)")}
        expected = {
            "record_id",
            "student_id",
            "week_start",
            "stress_level",
            "sleep_hours",
            "source_type",
        }
        assert expected <= cols
        con.close()

    def test_wellbeing_record_foreign_key(self, tmp_path, monkeypatch):
        """Verify wellbeing_record.student_id has FK to student"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO wellbeing_record(student_id, week_start, stress_level, sleep_hours, source_type) "
                "VALUES ('INVALID', '2025-01-01', 5, 7.5, 'survey')"
            )
            con.commit()
        con.close()


class TestAlertTable:
    """Test suite for alert table schema"""

    def test_alert_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify alert table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"] for row in con.execute("PRAGMA table_info(alert)")}
        expected = {
            "alert_id",
            "student_id",
            "alert_type",
            "reason",
            "created_at",
            "resolved",
        }
        assert expected <= cols
        con.close()

    def test_alert_foreign_key(self, tmp_path, monkeypatch):
        """Verify alert.student_id has FK to student"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO alert(student_id, alert_type, reason, created_at, resolved) "
                "VALUES ('INVALID', 'low_attendance', 'Too many absences', datetime('now'), 0)"
            )
            con.commit()
        con.close()


class TestRetentionRuleTable:
    """Test suite for retention_rule table schema"""

    def test_retention_rule_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify retention_rule table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"]
                for row in con.execute("PRAGMA table_info(retention_rule)")}
        expected = {"rule_id", "data_type", "retention_months", "is_active"}
        assert expected <= cols
        con.close()

    def test_retention_rule_insert_and_retrieve(self, tmp_path, monkeypatch):
        """Verify can insert and retrieve retention rules"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        con.execute(
            "INSERT INTO retention_rule(data_type, retention_months, is_active) "
            "VALUES ('attendance', 12, 1)"
        )
        con.commit()

        row = con.execute(
            "SELECT * FROM retention_rule WHERE data_type = 'attendance'"
        ).fetchone()
        assert row["retention_months"] == 12
        assert row["is_active"] == 1
        con.close()


class TestAuditLogTable:
    """Test suite for audit_log table schema"""

    def test_audit_log_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify audit_log table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        cols = {row["name"]
                for row in con.execute("PRAGMA table_info(audit_log)")}
        expected = {
            "log_id",
            "user_id",
            "entity_type",
            "entity_id",
            "action_type",
            "timestamp",
            "details",
        }
        assert expected <= cols
        con.close()

    def test_audit_log_insert_and_retrieve(self, tmp_path, monkeypatch):
        """Verify can insert and retrieve audit logs"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        con.execute(
            "INSERT INTO audit_log(user_id, entity_type, entity_id, action_type, timestamp, details) "
            "VALUES ('admin1', 'student', 'S001', 'CREATE', datetime('now'), 'Student created')"
        )
        con.commit()

        row = con.execute(
            "SELECT * FROM audit_log WHERE user_id = 'admin1'"
        ).fetchone()
        assert row["entity_type"] == "student"
        assert row["action_type"] == "CREATE"
        con.close()


class TestUserTable:
    """Test suite for user table schema"""

    def test_user_table_has_required_columns(self, tmp_path, monkeypatch):
        """Verify user table has all required columns"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        user_cols = {
            row["name"] for row in con.execute("PRAGMA table_info(user)")
        }
        assert {"user_id", "first_name", "lastname",
                "password_hash", "role"} <= user_cols
        con.close()

    def test_user_id_is_primary_key(self, tmp_path, monkeypatch):
        """Verify user_id is the primary key"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        pk_info = con.execute("PRAGMA table_info(user)").fetchall()
        user_id_col = next(row for row in pk_info if row["name"] == "user_id")
        assert user_id_col["pk"] == 1
        con.close()

    def test_user_insert_and_retrieve(self, tmp_path, monkeypatch):
        """Verify can insert and retrieve user records"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        con.execute(
            "INSERT INTO user(user_id, first_name, lastname, password_hash, role) "
            "VALUES ('admin1', 'Admin', 'User', 'hash123', 'admin')"
        )
        con.commit()

        row = con.execute(
            "SELECT * FROM user WHERE user_id = 'admin1'").fetchone()
        assert row["first_name"] == "Admin"
        assert row["role"] == "admin"
        con.close()

    def test_user_not_null_constraints(self, tmp_path, monkeypatch):
        """Verify NOT NULL constraints on user table"""
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO user(user_id, first_name, lastname, password_hash, role) "
                "VALUES ('user1', NULL, 'Lastname', 'hash', 'admin')"
            )
            con.commit()
        con.close()
