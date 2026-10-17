import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os, sys
import tempfile

# Füge das Verzeichnis hinzu, in dem dein Modul liegt
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Server/API'))
sys.path.insert(0, module_path)

class TestSqliteGetMeasPointId(unittest.TestCase):

    @patch('database_utils.get_sqlite3_connection')  # Mock the DB connection function
    @patch('database_utils.get_sqlite3_file_name_from_conf')  # Mock the SQLite file name generator
    def test_sqlite_get_meas_point_id_existing_point(self, mock_get_file_name, mock_get_connection):
        # Arrange
        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/db/'
        }
        mp_name = 'Temperature'
        dt = datetime(2024, 12, 15)

        mock_get_file_name.return_value = 'database_file.db'
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(42,)]  # Simulate existing measurement point with ID 42

        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = (mock_conn, mock_cursor)  # Simulate context manager for connection
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        # Act
        from database_utils import sqlite_get_meas_point_id
        mp_id = sqlite_get_meas_point_id(db_conf, mp_name, dt)

        # Assert
        self.assertEqual(mp_id, 42)
        mock_cursor.execute.assert_called_once_with("SELECT max(id) FROM meas_point WHERE name = ?", [mp_name])

    @patch('database_utils.get_sqlite3_connection')
    @patch('database_utils.get_sqlite3_file_name_from_conf')
    def test_sqlite_get_meas_point_id_new_point(self, mock_get_file_name, mock_get_connection):
        # Arrange
        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/db/'
        }
        mp_name = 'Pressure'
        dt = datetime(2024, 12, 15)

        mock_get_file_name.return_value = 'database_file.db'
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(None,)]  # Simulate no existing measurement point
        mock_cursor.lastrowid = 99  # Simulate newly inserted row ID

        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = (mock_conn, mock_cursor)  # Simulate context manager for connection
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        # Act
        from database_utils import sqlite_get_meas_point_id
        mp_id = sqlite_get_meas_point_id(db_conf, mp_name, dt)

        # Assert
        self.assertEqual(mp_id, 99)
        mock_cursor.execute.assert_any_call("SELECT max(id) FROM meas_point WHERE name = ?", [mp_name])
        mock_cursor.execute.assert_any_call("INSERT INTO meas_point (name) VALUES (?)", [mp_name])
        mock_conn.commit.assert_called_once()

    def test_raw_measurement_data_keeps_samples_per_measurement(self):
        from database_utils import get_meas_raw_data_from_sqlite_db, get_sqlite3_connection

        with tempfile.TemporaryDirectory() as db_directory:
            db_file = os.path.join(db_directory, '10-2026.sqlite')
            conn, cur = get_sqlite3_connection(db_file)
            try:
                cur.execute("INSERT INTO meas_point (id, name) VALUES (1, 'test-point')")
                cur.execute(
                    "INSERT INTO sensor (id, meas_point_id, name, tank_height, max_val, warn, alarm) "
                    "VALUES (1, 1, 'test-sensor', 100, 80, 70, 60)"
                )
                cur.execute(
                    "INSERT INTO measurement (id, dt, sensor_id) "
                    "VALUES (1, '2026-10-02T10:00:00', 1)"
                )
                cur.execute(
                    "INSERT INTO meas_val (measurement_id, value) "
                    "VALUES (1, 1), (1, 2), (1, 3)"
                )
                conn.commit()
            finally:
                conn.close()

            rows = get_meas_raw_data_from_sqlite_db(
                {'engine': 'sqlite', 'sqlite_path': db_directory},
                datetime(2026, 10, 1),
                datetime(2026, 10, 4),
                'test-point'
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['raw_values'], [1.0, 2.0, 3.0])
        self.assertEqual(rows[0]['meas_val'], 2.0)


if __name__ == '__main__':
    unittest.main()
