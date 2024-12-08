"""
Module Name: Wassermonitor2 API database functions

Description:
    This file provides the database functions for the wassermonitor API.
    It includes functions for:
        - Insert measurement data into the database
        - Read data from database.

Dependencies:
    - sqlite3  (for sqlite support)
    - pymysql (for mysql support)

Configuration:
    - Some parameters can be configured in the config_file ../config.cfg.

Author:
    - Carl Philipp Koppen (admin@wassermonitor.de)

"""

import pymysql
import sqlite3
from sqlite3 import Error
from datetime import datetime, timezone
import pytz

def get_mysql_connection(conf):
    """
    Establishes a connection to a MySQL database and returns the connection and cursor objects.

    Parameters:
    conf (dict): A dictionary containing the database connection parameters:
        - 'host' (str): The hostname or IP address of the MySQL server.
        - 'user' (str): The username to use for authentication.
        - 'pass' (str): The password to use for authentication.
        - 'db' (str): The name of the database to connect to.

    Returns:
    tuple: A tuple containing:
        - conn: The MySQL connection object.
        - cur: The MySQL cursor object.

    Example:
    >>> conf = {'host': 'localhost', 'user': 'root', 'pass': 'password', 'db': 'test_db'}
    >>> conn, cur = get_mysql_connection(conf)
    """
    conn = pymysql.connect(host=conf['host'], user=conf['user'], password=conf['pass'],
                            db=conf['db'], connect_timeout=60)
    cur = conn.cursor()
    return conn, cur

def get_sqlite3_connection(db_file):
    """
    Establishes a connection to an SQLite3 database, creates the database if it doesn't exist,
    and returns the connection and cursor objects.

    Parameters:
    db_file (str): The file path to the SQLite3 database file.

    Returns:
    tuple: A tuple containing:
        - conn: The SQLite3 connection object.
        - cur: The SQLite3 cursor object.

    Example:
    >>> db_file = 'example.db'
    >>> conn, cur = get_sqlite3_connection(db_file)
    """
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    create_sqlite_database(conn, cur)
    return conn, cur

def create_sqlite_database(conn, cur):
    """
    Creates the necessary tables in the SQLite3 database if they do not already exist.

    Parameters:
    conn: The SQLite3 connection object.
    cur: The SQLite3 cursor object.

    Tables Created:
    - measurement: Stores measurement data with fields for id, datetime, pi_name, sensor_id, and comment.
    - meas_val: Stores measurement values with fields for id, measurement_id, value, and comment.

    Example:
    >>> conn, cur = get_sqlite3_connection('example.db')
    >>> create_sqlite_database(conn, cur)
    """

    template = list()
    template.append("""
        CREATE TABLE IF NOT EXISTS measurement (
            id INTEGER NOT NULL PRIMARY KEY,
            dt DATETIME NOT NULL,
            pi_name VARCHAR(1024) NOT NULL,
            sensor_id INTEGER,
            comment TEXT    
        );
    """)

    template.append("""
        CREATE TABLE IF NOT EXISTS meas_val (
            id INTEGER NOT NULL PRIMARY KEY,
            measurement_id INTEGER NOT NULL REFERENCES measurement(id),
            value FLOAT NOT NULL,
            comment TEXT
        );
    """)

    try:
        for line in template:
            cur.execute(line)

        conn.commit()

    except Error as e:
        print(f"Database_creation: SQL Error: {e}\n {line}")


def insert_and_get_id(db_conf, dt, sql, sql_args):
    """
    Inserts a record into the database and returns the ID of the inserted record.

    Parameters:
    db_conf (dict): A dictionary containing the database configuration parameters:
        - 'engine' (str): The type of database engine (e.g., "sqlite").
        - 'sqlite_path' (str): The path to the SQLite database files.
    dt (datetime): The datetime object used to generate the SQLite file name.
    sql (str): The SQL query to execute.
    sql_args (tuple): The arguments to pass to the SQL query.

    Returns:
    int: The ID of the inserted record if successful.
    Exception: The exception object if an error occurs.

    Example:
    >>> db_conf = {'engine': 'sqlite', 'sqlite_path': '/path/to/db/'}
    >>> dt = datetime.now(timezone.utc) with timezone utc
    >>> sql = "INSERT INTO measurement (dt, pi_name) VALUES (?, ?)"
    >>> sql_args = (dt, 'sensor_1')
    >>> insert_id = insert_and_get_id(db_conf, dt, sql, sql_args)
    """
    if db_conf['engine'] == "sqlite":
        sqlite_file_name = db_conf['sqlite_path'] + get_sqlite3_file_name_from_conf(dt)
        try:
            conn, cur =get_sqlite3_connection(sqlite_file_name)
            cur.execute(sql, sql_args)
            ins_id = cur.lastrowid
            conn.commit()
        except Error as e:
            print("SQL ERROR: %s\n%s" % (e, sql))
            ins_id = None
            return e
        finally:
            conn.close()
        return ins_id


def insert_value(db_conf, val_dict):
    """
    Inserts a measurement and its associated values into the database.

    Parameters:
    db_conf (dict): A dictionary containing the database configuration parameters.
    val_dict (dict): A dictionary containing the measurement details and values:
        - 'datetime' (str): The datetime of the measurement in ISO format.
        - 'pi_name' (str): The name of the Raspberry Pi or device.
        - 'sensor_id' (int): The ID of the sensor.
        - 'values' (list): A list of measurement values to be inserted.

    Returns:
    bool: Always returns False.

    Example:
    >>> db_conf = {'engine': 'sqlite', 'sqlite_path': '/path/to/db/'}
    >>> val_dict = {
    ...     'datetime': '2024-12-05T07:11:32+00:00',
    ...     'pi_name': 'sensor_1',
    ...     'sensor_id': 1,
    ...     'values': [23.5, 24.0, 22.8]
    ... }
    >>> insert_value(db_conf, val_dict)
    False
    """

    #now = datetime.utcnow() # Decrepatet
    now = datetime.now(timezone.utc)
    now = now.replace(tzinfo=pytz.utc)
    # CREATE MEASUREMENT
    sql = ("""
        INSERT INTO measurement(
            dt, pi_name, sensor_id, comment
        ) VALUES (
            ?, ?, ?, ?
        ); 
    """)
    meas_dt = datetime.fromisoformat(val_dict['datetime'])
    meas_id = insert_and_get_id(
        db_conf,
        meas_dt,
        sql,
        [
            meas_dt,
            val_dict['pi_name'],
            val_dict['sensor_id'],
            f'received at {now.isoformat()}'
        ]
    )
    # INSERT VALUES
    sql = "INSERT INTO meas_val(measurement_id, value) VALUES ( ?, ?);"
    for value in val_dict['values']:
        x = insert_and_get_id(db_conf, meas_dt, sql, [meas_id, value])

    return False

def get_sqlite3_file_name_from_conf(dt):
    """
    Generates an SQLite3 file name based on the provided datetime object.

    Parameters:
    dt (datetime): The datetime object used to generate the file name.

    Returns:
    str: The generated SQLite3 file name in the format "month-year.sqlite".
    bool: Returns False if the input is not a datetime object.

    Example:
    >>> dt = datetime(2024, 12, 5)
    >>> get_sqlite3_file_name_from_conf(dt)
    '12-2024.sqlite'
    """


    if isinstance(dt, datetime):
        return f"{dt.month}-{dt.year}.sqlite"
    else:
        return False
