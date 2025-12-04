import sqlite3
import pytest

from ..src.Student_Wellbeing_App.core.database import connection as db_conn
from ..src.Student_Wellbeing_App.core.database import migrations


def _use_temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.sqlite3"
    monkeypatch.setattr(db_conn, "DB_PATH", db_file)
    monkeypatch.setattr(db_conn, "DB_NAME", db_file)
    # keep migrations prints/paths consistent
    monkeypatch.setattr(migrations, "DB_NAME", db_file)
    return db_file


class TestGetDbConnection:
    """Test suite for get_db_connection function"""

    def test_get_db_connection_returns_connection_object(self, tmp_path, monkeypatch):
        """Verify get_db_connection returns a valid sqlite3.Connection"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_connection()
        assert isinstance(con, sqlite3.Connection)
        con.close()

    def test_get_db_connection_enforces_foreign_keys(self, tmp_path, monkeypatch):
        """Verify foreign key constraints are enforced"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_connection()
        con.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
        con.execute(
            "CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER, "
            "FOREIGN KEY(parent_id) REFERENCES parent(id))"
        )

        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO child(parent_id) VALUES (999)")
        con.close()

    def test_get_db_connection_returns_row_objects(self, tmp_path, monkeypatch):
        """Verify row_factory is set to sqlite3.Row for dict-like access"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_connection()
        con.execute("CREATE TABLE demo(id INTEGER)")
        con.execute("INSERT INTO demo(id) VALUES (1)")
        row = con.execute("SELECT * FROM demo").fetchone()

        assert isinstance(row, sqlite3.Row)
        assert row["id"] == 1
        con.close()

    def test_get_db_connection_row_dict_access(self, tmp_path, monkeypatch):
        """Verify Row objects support both dict and index access"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_connection()
        con.execute("CREATE TABLE test(col1 TEXT, col2 INTEGER)")
        con.execute("INSERT INTO test(col1, col2) VALUES ('hello', 42)")
        row = con.execute("SELECT * FROM test").fetchone()

        # Dict access
        assert row["col1"] == "hello"
        assert row["col2"] == 42
        # Index access
        assert row[0] == "hello"
        assert row[1] == 42
        con.close()

    def test_get_db_connection_independent_instances(self, tmp_path, monkeypatch):
        """Verify each call returns a new independent connection"""
        _use_temp_db(tmp_path, monkeypatch)
        con1 = db_conn.get_db_connection()
        con2 = db_conn.get_db_connection()

        assert con1 is not con2
        con1.close()
        con2.close()

    def test_get_db_connection_can_execute_queries(self, tmp_path, monkeypatch):
        """Verify connection can execute and commit queries"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_connection()
        con.execute("CREATE TABLE test(id INTEGER PRIMARY KEY, value TEXT)")
        con.execute("INSERT INTO test(id, value) VALUES (1, 'test')")
        con.commit()

        cursor = con.execute("SELECT * FROM test WHERE id = 1")
        row = cursor.fetchone()
        assert row["value"] == "test"
        con.close()

    def test_get_db_connection_handles_null_values(self, tmp_path, monkeypatch):
        """Verify NULL values are properly handled"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_connection()
        con.execute("CREATE TABLE test(id INTEGER, value TEXT)")
        con.execute("INSERT INTO test(id, value) VALUES (1, NULL)")
        row = con.execute("SELECT * FROM test").fetchone()

        assert row["id"] == 1
        assert row["value"] is None
        con.close()


class TestGetDbPool:
    """Test suite for get_db_pool function (backwards-compatibility shim)"""

    def test_get_db_pool_returns_connection(self, tmp_path, monkeypatch):
        """Verify get_db_pool returns a connection object"""
        _use_temp_db(tmp_path, monkeypatch)
        pool = db_conn.get_db_pool()
        assert isinstance(pool, sqlite3.Connection)
        pool.close()

    def test_get_db_pool_has_foreign_keys_enabled(self, tmp_path, monkeypatch):
        """Verify pool connection also enforces foreign keys"""
        _use_temp_db(tmp_path, monkeypatch)
        con = db_conn.get_db_pool()
        con.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
        con.execute(
            "CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER, "
            "FOREIGN KEY(parent_id) REFERENCES parent(id))"
        )

        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO child(parent_id) VALUES (999)")
        con.close()

    def test_get_db_pool_independent_from_get_db_connection(self, tmp_path, monkeypatch):
        """Verify pool and direct connection calls return different instances"""
        _use_temp_db(tmp_path, monkeypatch)
        con1 = db_conn.get_db_connection()
        con2 = db_conn.get_db_pool()

        assert con1 is not con2
        con1.close()
        con2.close()
