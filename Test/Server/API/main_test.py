import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os, sys

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


if __name__ == '__main__':
    unittest.main()
