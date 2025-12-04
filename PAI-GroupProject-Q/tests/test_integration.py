"""
Integration tests for database operations across multiple tables.
Tests realistic workflows involving multiple table interactions.
"""

import sqlite3
import pytest

from Student_Wellbeing_App.core.database import connection as db_conn
from Student_Wellbeing_App.core.database import migrations


def _use_temp_db(tmp_path, monkeypatch):
    """Helper to set up isolated temp database for each test"""
    db_file = tmp_path / "integration.sqlite3"
    monkeypatch.setattr(db_conn, "DB_PATH", db_file)
    monkeypatch.setattr(db_conn, "DB_NAME", db_file)
    monkeypatch.setattr(migrations, "DB_NAME", db_file)
    return db_file


class TestStudentWorkflow:
    """Integration tests for complete student workflows"""

    def test_create_student_and_track_attendance(self, tmp_path, monkeypatch):
        """
        Workflow: Create a student and record multiple attendance sessions
        Verifies: student insert, attendance inserts, FK constraint
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Create a student
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S001', 'Alice', 'Johnson', 'alice@university.edu', 'securepass', 1)"
        )
        con.commit()

        # Record attendance sessions
        sessions = [
            ("2025-01-06", "session1", "present"),
            ("2025-01-13", "session2", "present"),
            ("2025-01-20", "session3", "absent"),
            ("2025-01-27", "session4", "present"),
        ]

        for date, sess_id, status in sessions:
            con.execute(
                "INSERT INTO attendance(student_id, session_date, session_id, status) "
                "VALUES (?, ?, ?, ?)",
                ("S001", date, sess_id, status),
            )
        con.commit()

        # Verify attendance records
        records = con.execute(
            "SELECT * FROM attendance WHERE student_id = 'S001' ORDER BY session_date"
        ).fetchall()
        assert len(records) == 4
        assert records[0]["session_id"] == "session1"
        assert records[2]["status"] == "absent"

        con.close()

    def test_create_student_with_submissions(self, tmp_path, monkeypatch):
        """
        Workflow: Create a student and assessment, then submit assignments
        Verifies: student/assessment inserts, submission inserts with FK constraints
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Create student
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S002', 'Bob', 'Smith', 'bob@university.edu', 'pass123', 2)"
        )

        # Create assessment
        con.execute(
            "INSERT INTO assessment(module_code, title, due_date, weight) "
            "VALUES ('CS101', 'Assignment 1', '2025-02-15', 0.3)"
        )
        con.execute(
            "INSERT INTO assessment(module_code, title, due_date, weight) "
            "VALUES ('CS101', 'Final Exam', '2025-05-20', 0.7)"
        )
        con.commit()

        # Get assessment IDs
        assessments = con.execute(
            "SELECT assessment_id FROM assessment ORDER BY due_date"
        ).fetchall()
        assert len(assessments) == 2

        # Submit assignments
        con.execute(
            "INSERT INTO submission(student_id, assessment_id, submitted_at, status, mark) "
            "VALUES ('S002', ?, datetime('2025-02-10'), 'submitted', 85.5)",
            (assessments[0]["assessment_id"],),
        )
        con.execute(
            "INSERT INTO submission(student_id, assessment_id, submitted_at, status, mark) "
            "VALUES ('S002', ?, datetime('2025-05-15'), 'submitted', 92.0)",
            (assessments[1]["assessment_id"],),
        )
        con.commit()

        # Verify submissions
        submissions = con.execute(
            "SELECT * FROM submission WHERE student_id = 'S002'"
        ).fetchall()
        assert len(submissions) == 2
        assert submissions[0]["mark"] == 85.5
        assert submissions[1]["mark"] == 92.0

        con.close()

    def test_student_wellbeing_tracking(self, tmp_path, monkeypatch):
        """
        Workflow: Track student wellbeing metrics over multiple weeks
        Verifies: repeated inserts, numeric data handling
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Create student
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S003', 'Charlie', 'Brown', 'charlie@university.edu', 'pwd456', 1)"
        )
        con.commit()

        # Record wellbeing over 4 weeks
        weeks = [
            ("2025-01-06", 6, 7.5, "survey"),
            ("2025-01-13", 7, 6.5, "survey"),
            ("2025-01-20", 8, 5.0, "manual"),
            ("2025-01-27", 9, 4.5, "manual"),
        ]

        for week_start, stress, sleep, source in weeks:
            con.execute(
                "INSERT INTO wellbeing_record(student_id, week_start, stress_level, sleep_hours, source_type) "
                "VALUES (?, ?, ?, ?, ?)",
                ("S003", week_start, stress, sleep, source),
            )
        con.commit()

        # Verify trend
        records = con.execute(
            "SELECT * FROM wellbeing_record WHERE student_id = 'S003' ORDER BY week_start"
        ).fetchall()
        assert len(records) == 4
        # Stress levels should be increasing
        stress_levels = [r["stress_level"] for r in records]
        assert stress_levels == [6, 7, 8, 9]

        con.close()

    def test_student_alert_workflow(self, tmp_path, monkeypatch):
        """
        Workflow: Generate and resolve alerts for a student
        Verifies: alert creation, update operations, boolean flags
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Create student
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S004', 'Diana', 'Prince', 'diana@university.edu', 'secure123', 2)"
        )
        con.commit()

        # Create alert
        con.execute(
            "INSERT INTO alert(student_id, alert_type, reason, created_at, resolved) "
            "VALUES ('S004', 'low_attendance', 'Missing 3 consecutive sessions', datetime('2025-01-25'), 0)"
        )
        con.commit()

        alert_id = con.execute(
            "SELECT alert_id FROM alert WHERE student_id = 'S004'"
        ).fetchone()["alert_id"]

        # Verify unresolved
        alert = con.execute(
            "SELECT * FROM alert WHERE alert_id = ?", (alert_id,)).fetchone()
        assert alert["resolved"] == 0

        # Resolve alert
        con.execute(
            "UPDATE alert SET resolved = 1 WHERE alert_id = ?", (alert_id,)
        )
        con.commit()

        # Verify resolved
        alert = con.execute(
            "SELECT * FROM alert WHERE alert_id = ?", (alert_id,)).fetchone()
        assert alert["resolved"] == 1

        con.close()


class TestAuditTrail:
    """Integration tests for audit logging across operations"""

    def test_audit_log_user_operations(self, tmp_path, monkeypatch):
        """
        Workflow: Create admin user and log audit events for student creation
        Verifies: user table, audit_log table interactions
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Create admin user
        con.execute(
            "INSERT INTO user(user_id, first_name, lastname, password_hash, role) "
            "VALUES ('admin1', 'System', 'Administrator', 'hash_admin', 'admin')"
        )
        con.commit()

        # Create student and log it
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S005', 'Eve', 'Wilson', 'eve@university.edu', 'pass789', 1)"
        )

        con.execute(
            "INSERT INTO audit_log(user_id, entity_type, entity_id, action_type, timestamp, details) "
            "VALUES ('admin1', 'student', 'S005', 'CREATE', datetime('now'), 'Student S005 created')"
        )
        con.commit()

        # Verify audit trail
        logs = con.execute(
            "SELECT * FROM audit_log WHERE user_id = 'admin1'"
        ).fetchall()
        assert len(logs) == 1
        assert logs[0]["entity_id"] == "S005"
        assert logs[0]["action_type"] == "CREATE"

        con.close()


class TestDataRetention:
    """Integration tests for retention rules and data policies"""

    def test_retention_rule_configuration(self, tmp_path, monkeypatch):
        """
        Workflow: Configure and verify retention rules for different data types
        Verifies: retention_rule table, multiple rule types
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Configure retention rules
        rules = [
            ("attendance", 12, 1),
            ("wellbeing_records", 24, 1),
            ("assessments", 36, 1),
            ("temp_data", 3, 0),  # inactive rule
        ]

        for data_type, months, is_active in rules:
            con.execute(
                "INSERT INTO retention_rule(data_type, retention_months, is_active) "
                "VALUES (?, ?, ?)",
                (data_type, months, is_active),
            )
        con.commit()

        # Verify active rules
        active_rules = con.execute(
            "SELECT * FROM retention_rule WHERE is_active = 1"
        ).fetchall()
        assert len(active_rules) == 3
        assert any(r["data_type"] == "attendance" for r in active_rules)

        # Verify inactive rules exist but aren't applied
        all_rules = con.execute("SELECT * FROM retention_rule").fetchall()
        assert len(all_rules) == 4

        con.close()


class TestComplexQueryScenarios:
    """Integration tests for complex queries across multiple tables"""

    def test_student_performance_summary(self, tmp_path, monkeypatch):
        """
        Scenario: Get performance summary for a student (attendance + submissions + wellbeing)
        Verifies: complex joins and aggregations
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Setup: create student, assessments, and data
        con.execute(
            "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
            "VALUES ('S006', 'Frank', 'Miller', 'frank@university.edu', 'pass999', 1)"
        )

        # Insert attendance records
        for i in range(10):
            status = "present" if i < 8 else "absent"
            con.execute(
                "INSERT INTO attendance(student_id, session_date, session_id, status) "
                "VALUES ('S006', ?, ?, ?)",
                (f"2025-01-{6 + i:02d}", f"s{i+1}", status),
            )

        # Insert assessment and submission
        con.execute(
            "INSERT INTO assessment(module_code, title, due_date, weight) "
            "VALUES ('CS101', 'Test 1', '2025-02-01', 0.4)"
        )
        assessment_id = con.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        con.execute(
            "INSERT INTO submission(student_id, assessment_id, submitted_at, status, mark) "
            "VALUES ('S006', ?, datetime('now'), 'submitted', 88.0)",
            (assessment_id,),
        )

        # Insert wellbeing data
        con.execute(
            "INSERT INTO wellbeing_record(student_id, week_start, stress_level, sleep_hours, source_type) "
            "VALUES ('S006', '2025-01-06', 5, 7.5, 'survey')"
        )
        con.commit()

        # Query: Student attendance rate
        attendance_summary = con.execute(
            """
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                COUNT(*) as total
            FROM attendance 
            WHERE student_id = 'S006'
            """
        ).fetchone()
        assert attendance_summary["present_count"] == 8
        assert attendance_summary["absent_count"] == 2
        assert attendance_summary["total"] == 10

        # Query: Submission marks
        submission_summary = con.execute(
            """
            SELECT AVG(mark) as avg_mark, COUNT(*) as submission_count
            FROM submission
            WHERE student_id = 'S006'
            """
        ).fetchone()
        assert submission_summary["avg_mark"] == 88.0
        assert submission_summary["submission_count"] == 1

        # Query: Latest wellbeing status
        wellbeing_latest = con.execute(
            """
            SELECT stress_level, sleep_hours
            FROM wellbeing_record
            WHERE student_id = 'S006'
            ORDER BY week_start DESC
            LIMIT 1
            """
        ).fetchone()
        assert wellbeing_latest["stress_level"] == 5
        assert wellbeing_latest["sleep_hours"] == 7.5

        con.close()

    def test_multiple_students_comparison(self, tmp_path, monkeypatch):
        """
        Scenario: Compare metrics across multiple students
        Verifies: GROUP BY queries, multiple student records
        """
        _use_temp_db(tmp_path, monkeypatch)
        migrations.run_migrations()

        con = db_conn.get_db_connection()

        # Create 3 students
        students = [
            ("S101", "Grace", "Lee"),
            ("S102", "Henry", "Taylor"),
            ("S103", "Iris", "Anderson"),
        ]

        for sid, fname, lname in students:
            con.execute(
                "INSERT INTO student(student_id, first_name, lastname, email, password, year) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sid, fname, lname, f"{fname.lower()}@uni.edu", "pass", 1),
            )

        # Add attendance for each
        for sid in ["S101", "S102", "S103"]:
            for i in range(10):
                con.execute(
                    "INSERT INTO attendance(student_id, session_date, session_id, status) "
                    "VALUES (?, ?, ?, ?)",
                    (sid, f"2025-01-{6 + i:02d}", f"s{i}",
                     "present" if i < 8 else "absent"),
                )

        con.commit()

        # Query: Attendance rates by student
        summary = con.execute(
            """
            SELECT 
                student_id,
                COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as attendance_rate
            FROM attendance
            GROUP BY student_id
            ORDER BY attendance_rate DESC
            """
        ).fetchall()

        assert len(summary) == 3
        assert summary[0]["attendance_rate"] == 80.0

        con.close()
