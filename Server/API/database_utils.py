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
import os.path

import pandas as pd
import pymysql
import sqlite3
from sqlite3 import Error
from datetime import datetime, timezone, timedelta
import pandas as pd
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
        CREATE TABLE IF NOT EXISTS meas_point (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(1024) NOT NULL
        );
    """)

    template.append("""
        CREATE TABLE IF NOT EXISTS sensor (
            id INTEGER NOT NULL PRIMARY KEY,
            meas_point_id INTEGER NOT NULL REFERENCES meas_point(id),
            name VARCHAR(1024) NOT NULL,
            max_val FLOAT NOT NULL,
            warn FLOAT NOT NULL,
            alarm FLOAT NOT NULL
        );
    """)

    template.append("""
        CREATE TABLE IF NOT EXISTS measurement (
            id INTEGER NOT NULL PRIMARY KEY,
            dt DATETIME NOT NULL,
            sensor_id INTEGER NOT NULL REFERENCES sensor(id),
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

def sqlite_get_sensor_id(db_conf, mp_id, s_name, s_max_val, s_warn, s_alarm, dt):
    if db_conf['engine'] == "sqlite":
        sqlite_file_name = db_conf['sqlite_path'] + get_sqlite3_file_name_from_conf(dt)
        try:
            # Check if Sensor exists
            sql = "SELECT max(id) FROM sensor WHERE meas_point_id = ? AND name = ? AND max_val = ? AND warn = ? AND alarm = ?"

            conn, cur = get_sqlite3_connection(sqlite_file_name)
            cur.execute(sql, [mp_id, s_name, s_max_val, s_warn, s_alarm])
            res = cur.fetchall()
            if res == None or res == [] or res[0][0] == None: # If not: Insert Sensor
                sql = "INSERT INTO sensor(meas_point_id, name, max_val, warn, alarm) VALUES (?, ?, ?, ?, ?)"
                cur.execute(sql, [mp_id, s_name, s_max_val, s_warn, s_alarm])
                s_id = cur.lastrowid
                conn.commit()
            else:
                s_id = res[0][0]
        except Error as e:
            print("SQL ERROR: %s\n%s" % (e, sql))
            s_id = None
            return e
        finally:
            conn.close()
        return s_id

def sqlite_get_meas_point_id(db_conf, mp_name,dt):
    if db_conf['engine'] == "sqlite":
        sqlite_file_name = db_conf['sqlite_path'] + get_sqlite3_file_name_from_conf(dt)
        try:
            # Check if Meas Point exists
            sql = "SELECT max(id) FROM meas_point WHERE name = ?"
            conn, cur = get_sqlite3_connection(sqlite_file_name)
            cur.execute(sql, [mp_name])
            res = cur.fetchall()

            if res == None or res == [] or res[0][0] == None: # If not Insert Meas Point
                sql = "INSERT INTO meas_point (name) VALUES (?)"
                cur.execute(sql, [mp_name])
                mp_id = cur.lastrowid
                conn.commit()
            else:
                mp_id = res[0][0]
        except Error as e:
            print("SQL ERROR: %s\n%s" % (e, sql))
            mp_id = None
            return e
        finally:
            conn.close()
        return mp_id


def insert_value(db_conf, val_dict):
    meas_dt = datetime.fromisoformat(val_dict['datetime'])
    mp_id = sqlite_get_meas_point_id(db_conf, val_dict['meas_point'], meas_dt)
    s_id = sqlite_get_sensor_id(
        db_conf,
        mp_id,
        val_dict['sensor_name'],
        val_dict['max_val'],
        val_dict['warn'],
        val_dict['alarm'],
        meas_dt
    )
    now = datetime.now(timezone.utc)
    now = now.replace(tzinfo=pytz.utc)
    # CREATE MEASUREMENT
    sql = ("""
        INSERT INTO measurement(
            dt, sensor_id, comment
        ) VALUES (
            ?, ?, ?
        ); 
    """)

    meas_id = insert_and_get_id(
        db_conf,
        meas_dt,
        sql,
        [
            meas_dt,
            s_id,
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

def get_months_between(start_date, end_date):
    """
    Generate a list of months between two datetime objects in "%m-%Y" format.

    Args:
        start_date (datetime): The start date.
        end_date (datetime): The end date.

    Returns:
        list: A list of strings representing the months in "%m-%Y" format.
    """
    # Ensure start_date is before end_date
    if start_date > end_date:
        raise ValueError("start_date must be earlier than or equal to end_date")

    months = []
    current = start_date.replace(day=1)  # Start at the beginning of the first month

    while current <= end_date:
        months.append(current.strftime("%m-%Y"))
        # Increment by one month
        next_month = current.month % 12 + 1
        next_year = current.year + (current.month // 12)
        current = current.replace(month=next_month, year=next_year)

    return months

def get_meas_data_from_sqlite_db(db_conf, dt_begin = None, dt_end = None):
    """
       Retrieves measurement data from an SQLite database within a specified date range.

       This function connects to an SQLite database specified in the `db_conf` dictionary,
       executes a query to fetch measurement data for each sensor within the date range
       defined by `dt_begin` and `dt_end`, and returns the results as a pandas DataFrame.

       Parameters:
       db_conf (dict): A dictionary containing the database configuration. It must include:
           - 'engine': A string specifying the database engine. Must be 'sqlite'.
           - 'sqlite_path': A string specifying the path to the database directory.
       dt_begin (datetime, optional): The start datetime for the data retrieval. Defaults to 60 days before `dt_end`.
       dt_end (datetime, optional): The end datetime for the data retrieval. Defaults to the current datetime.

       Returns:
       pandas.DataFrame: A DataFrame containing the measurement data within the specified date range.
       The DataFrame has the following columns:
           - 'dt': The datetime of the measurement.
           - 'sensor_id': The ID of the sensor.
           - 'pi_name': The name of the PI.
           - 'value': The average value of the measurements.

       Raises:
       ValueError: If the 'engine' specified in `db_conf` is not 'sqlite'.
       ValueError: If `dt_begin` or `dt_end` are not datetime objects.
       ValueError: If `dt_begin` is after `dt_end`.

       Example:
       >>> db_conf = {'engine': 'sqlite', 'sqlite_path': '/path/to/db/'}
       >>> df = get_meas_data_from_sqlite_db(db_conf, dt_begin=datetime(2024, 1, 1), dt_end=datetime(2024, 2, 1))
       >>> print(df)
    """

    if not db_conf['engine'] == 'sqlite':
        raise ValueError("Invalid Database function call: This functions is only for sqlite3 approach. Please configure it in your config.cfg file.")

    if dt_end == None:
        dt_end = datetime.now(timezone.utc)
        dt_end = dt_end.replace(tzinfo=pytz.utc)

    if dt_begin == None:
        dt_begin = dt_end - timedelta(days=60)

    if not isinstance(dt_begin, datetime) and not isinstance(dt_end, datetime):
        raise ValueError("Invalid input: dt_begin and dt_end have to be type of datetime!")

    if dt_begin > dt_end:
        raise ValueError(f"Invalid input: dt_begin ({dt_begin}) has to be before dt_end ({dt_end})!")
    sql = """
        SELECT m.id,m.dt, mp.name, s.name, s.max_val, s.warn, s.alarm, AVG(v.value)
        FROM meas_val v 
        INNER JOIN measurement m ON v.measurement_id=m.id 
        INNER JOIN sensor s ON m.sensor_id = s.id 
        INNER JOIN meas_point mp ON s.meas_point_id = mp.id 
        WHERE m.dt > ? AND m.dt < ?
        GROUP BY m.dt
    """

    output = pd.DataFrame()

    for m in get_months_between(dt_begin, dt_end):
        db_path = f"{db_conf['sqlite_path']}/{m}.sqlite"
        if os.path.exists(db_path):
            conn, cur = get_sqlite3_connection(db_path)
            cur.execute(sql,[dt_begin, dt_end])
            res = pd.DataFrame(cur.fetchall())
            res.columns = ['mid','dt', 'mpName', 'sensorId', 'max_val', 'warn', 'alarm', 'meas_val']
            conn.close()
            output = pd.concat([output, res], ignore_index=True)
    output['value'] = round(output['max_val'] - output['meas_val'], 1)
    return output

def get_latest_database_file(path):
    """
        Retrieves the latest SQLite database file from a specified directory.

        This function scans the specified directory for SQLite database files,
        extracts the date from the filenames, and returns the filename of the
        most recent database file.

        Parameters:
        path (str): The path to the directory containing the SQLite database files.

        Returns:
        str: The filename of the latest SQLite database file in the format 'MM-YYYY.sqlite'.

        Example:
        >>> latest_db_file = get_latest_database_file('/path/to/db/')
        >>> print(latest_db_file)
        '12-2024.sqlite'
    """

    datetime_list = []
    for file in os.listdir(path):
        if file.endswith(".sqlite"):
            datetime_list.append(
                datetime.strptime(
                    file.replace(".sqlite",""),
                    "%m-%Y"
                )
            )
    return max(datetime_list).strftime("%m-%Y.sqlite")

def assign_color(value, warn, alarm):
    if value < alarm:
        #return "red"
        return 'alarm'
    elif value < warn:
        #return "orange"
        return 'warning'
    else:
        #return "#0055bb"
        return 'normal'

def get_last_meas_data_from_sqlite_db(db_conf):
    """

    """

    if not db_conf['engine'] == 'sqlite':
        raise ValueError("Invalid Database function call: This functions is only for sqlite3 approach. Please configure it in your config.cfg file.")
    db_path = db_conf['sqlite_path'] + get_latest_database_file(db_conf['sqlite_path'])

    sql = """
        SELECT m.id,m.dt, mp.name, s.name, s.max_val, s. warn, s.alarm, AVG(v.value)
        FROM meas_val v 
        INNER JOIN measurement m ON v.measurement_id=m.id 
        INNER JOIN sensor s ON m.sensor_id = s.id 
        INNER JOIN meas_point mp ON s.meas_point_id = mp.id 
        WHERE m.id IN (SELECT max(id) FROM measurement GROUP BY sensor_id)
        GROUP BY m.dt;
    """
    output = {}
    if os.path.exists(db_path):
        conn, cur = get_sqlite3_connection(db_path)
        cur.execute(sql)
        res = cur.fetchall()
        for row in res:
            if not row[2] in output:
                output[row[2]] = {}
            if not row[3] in output[row[2]]:
                output[row[2]][row[3]] = {}
            output[row[2]][row[3]]['dt'] = row[1]
            output[row[2]][row[3]]['warn'] = row[5]
            output[row[2]][row[3]]['alarm'] = row[6]
            output[row[2]][row[3]]['max_val'] = row[4]
            output[row[2]][row[3]]['value'] = round(row[4] - row[7],1)
            output[row[2]][row[3]]['color'] = assign_color(
                output[row[2]][row[3]]['value'],
                row[5],
                row[6]
            )
        #res.columns = ['dt', 'pi_name', 'sensor_id', 'value']
        #res['value'] = 158.0 - res['value']
        #conn.close()
        #return res
    return output


#if __name__ == '__main__':
#    print(
 #       get_last_meas_data_from_sqlite_db(
#            {
#                'engine': 'sqlite',
#                'path': "../../Test/Server/Data/"
#            }
#        )
#    )