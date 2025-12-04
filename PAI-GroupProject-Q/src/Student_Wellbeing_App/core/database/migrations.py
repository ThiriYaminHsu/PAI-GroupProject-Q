import os
from datetime import datetime

from .connection import (
    get_db_connection,
    DB_NAME,
)


def run_migrations():
    # Connect using the same helper + same DB path as the rest of the app
    conn = get_db_connection()
    cursor = conn.cursor()

    print("DB file path:", DB_NAME)
    print("DB file exists:", os.path.exists(DB_NAME))

    # Create tables based on ERD
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student (
        student_id TEXT PRIMARY KEY,
        first_name TEXT,
        lastname   TEXT,
        email      TEXT UNIQUE,
        password   TEXT,
        year       INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id    TEXT,
        session_date  DATE,
        session_id    TEXT,
        status        TEXT,
        FOREIGN KEY (student_id) REFERENCES student(student_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessment (
        assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_code   TEXT,
        title         TEXT,
        due_date      DATE,
        weight        REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submission (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id    TEXT,
        assessment_id INTEGER,
        submitted_at  DATETIME,
        status        TEXT,
        mark          REAL,
        FOREIGN KEY (student_id)    REFERENCES student(student_id),
        FOREIGN KEY (assessment_id) REFERENCES assessment(assessment_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wellbeing_record (
        record_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id   TEXT,
        week_start   DATE,
        stress_level INTEGER,
        sleep_hours  REAL,
        source_type  TEXT,
        FOREIGN KEY (student_id) REFERENCES student(student_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert (
        alert_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  TEXT,
        alert_type  TEXT,
        reason      TEXT,
        created_at  DATETIME,
        resolved    INTEGER,   -- 0/1 as BOOLEAN
        FOREIGN KEY (student_id) REFERENCES student(student_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retention_rule (
        rule_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type        TEXT,
        retention_months INTEGER,
        is_active        INTEGER   -- 0/1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT,
        entity_type TEXT,
        entity_id   INTEGER,
        action_type TEXT,
        timestamp   DATETIME,
        details     TEXT
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            user_id       TEXT PRIMARY KEY,
            first_name    TEXT NOT NULL,
            lastname      TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role          TEXT NOT NULL
        );
        """)

    conn.commit()
    print(f"[{datetime.utcnow()}] Migrations completed successfully on {DB_NAME}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_migrations()
