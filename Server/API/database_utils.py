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
    - scipy.signal (for signale processing)

Configuration:
    - Some parameters can be configured in the config_file ../config.cfg.

Author:
    - Carl Philipp Koppen (admin@wassermonitor.de)

"""
import os.path

import numpy
import pandas as pd
import pymysql
import sqlite3
from sqlite3 import Error
from datetime import datetime, timezone, timedelta
import pandas as pd
import pytz
import numpy as np
from scipy import signal

def get_mysql_connection(conf):
    """
    Establishes a connection to a MySQL database and returns the connection and cursor objects.

    :param conf: A dictionary containing the database connection parameters:
        - 'host' (str): The hostname or IP address of the MySQL server.
        - 'user' (str): The username to use for authentication.
        - 'pass' (str): The password to use for authentication.
        - 'db' (str): The name of the database to connect to.
    :type conf: dict

    :returns: A tuple containing:
        - `conn`: The MySQL connection object.
        - `cur`: The MySQL cursor object.
    :rtype: tuple

    **Example usage**::

        conf = {'host': 'localhost', 'user': 'root', 'pass': 'password', 'db': 'test_db'}
        conn, cur = get_mysql_connection(conf)
    """

    conn = pymysql.connect(host=conf['host'], user=conf['user'], password=conf['pass'],
                            db=conf['db'], connect_timeout=60)
    cur = conn.cursor()
    return conn, cur


def get_sqlite3_connection(db_file):
    """
    Establishes a connection to an SQLite3 database, creates the database if it doesn't exist,
    and returns the connection and cursor objects.

    :param db_file: The file path to the SQLite3 database file.
    :type db_file: str

    :returns: A tuple containing:
        - `conn`: The SQLite3 connection object.
        - `cur`: The SQLite3 cursor object.
    :rtype: tuple

    **Example usage**::

        db_file = 'example.db'
        conn, cur = get_sqlite3_connection(db_file)
    """
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    create_sqlite_database(conn, cur)
    return conn, cur

def create_sqlite_database(conn, cur):
    """
    Creates the necessary tables in the SQLite3 database if they do not already exist.

    This function checks the SQLite3 database and creates the following tables if they are not already present:
    - `meas_point`: Stores measurement point data, including the point's ID and name.
    - `sensor`: Stores sensor data, including the sensor's ID, measurement point ID, name, tank height, maximum value, warning threshold, and alarm threshold.
    - `measurement`: Stores measurement data, including the measurement's ID, datetime, sensor ID, and a comment.
    - `meas_val`: Stores measurement values, including the value of the measurement and any associated comment.
    - `messages`: Stores message data, including a timestamp, signal and email targets, message text, and alarm/warning flags.

    :param conn: The SQLite3 connection object.
    :type conn: sqlite3.Connection
    :param cur: The SQLite3 cursor object.
    :type cur: sqlite3.Cursor

    :raises Error: If there is an error while executing the SQL commands.

    **Example usage**::

        conn, cur = get_sqlite3_connection('example.db')
        create_sqlite_database(conn, cur)
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
            tank_height FLOAT NOT NULL,
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

    template.append("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER NOT NULL PRIMARY KEY,
            dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            signal_target VARCHAR(1024) NOT NULL DEFAULT '',
            email_target VARCHAR(1024) NOT NULL DEFAULT '',
            telegram_target VARCHAR(1024) NOT NULL DEFAULT '',
            message_text TEXT NOT NULL DEFAULT '',
            warn INTEGER NOT NULL DEFAULT 0,
            alarm INTEGER NOT NULL DEFAULT 0,
            dewarn INTEGER NOT NULL DEFAULT 0,
            dealarm INTEGER NOT NULL DEFAULT 0,
            error TEXT
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

def sqlite_get_sensor_id(db_conf, mp_id, s_name, s_tank_height, s_max_val, s_warn, s_alarm, dt):
    """
    Retrieves or inserts a sensor ID based on the sensor details.

    This function checks if a sensor with the given name, measurement point ID,
    maximum value, warning threshold, and alarm threshold already exists in the
    SQLite database. If the sensor exists, it retrieves the corresponding ID.
    If it does not exist, the function inserts a new record for the sensor and
    returns the newly inserted ID.

    :param db_conf: A dictionary containing the database configuration. It should have the following keys:
        - `engine` (str): Should be `'sqlite'` for this function to work.
        - `sqlite_path` (str): The file path to the SQLite database directory.
    :type db_conf: dict

    :param mp_id: The ID of the measurement point to which the sensor is associated.
    :type mp_id: int

    :param s_name: The name of the sensor.
    :type s_name: str

    :param s_tank_height: The height of the tank.
    :type s_tank_height: float

    :param s_max_val: The maximum allowed value for the sensor.
    :type s_max_val: float

    :param s_warn: The warning threshold for the sensor.
    :type s_warn: float

    :param s_alarm: The alarm threshold for the sensor.
    :type s_alarm: float

    :param dt: The datetime object used to derive the SQLite file name from the configuration.
    :type dt: datetime

    :returns: The ID of the sensor. If the sensor does not exist, it is created and the new ID is returned.
    :rtype: int

    :raises Error: If any SQLite database errors occur during the query or insertion.

    :example:
        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/db/'
        }

        mp_id = 1

        s_name = 'TemperatureSensor'

        s_tank_height = 120

        s_max_val = 100.0

        s_warn = 80.0

        s_alarm = 90.0

        dt = datetime(2024, 12, 15)

        s_id = sqlite_get_sensor_id(db_conf, mp_id, s_name, s_max_val, s_warn, s_alarm, dt)

    """

    if db_conf['engine'] == "sqlite":
        sqlite_file_name = db_conf['sqlite_path'] + get_sqlite3_file_name_from_conf(dt)
        try:
            # Check if Sensor exists
            sql = "SELECT max(id) FROM sensor WHERE meas_point_id = ? AND name = ? AND tank_height = ? AND max_val = ? AND warn = ? AND alarm = ?"

            conn, cur = get_sqlite3_connection(sqlite_file_name)
            cur.execute(sql, [mp_id, s_name, s_tank_height, s_max_val, s_warn, s_alarm])
            res = cur.fetchall()
            if res == None or res == [] or res[0][0] == None: # If not: Insert Sensor
                sql = "INSERT INTO sensor(meas_point_id, name, tank_height, max_val, warn, alarm) VALUES (?, ?, ?, ?, ?, ?)"
                cur.execute(sql, [mp_id, s_name, s_tank_height, s_max_val, s_warn, s_alarm])
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
    """
    Retrieves or inserts a measurement point ID based on the measurement point name.

    This function checks if a measurement point with the given name already exists in the
    SQLite database. If the measurement point exists, it retrieves the corresponding ID.
    If it does not exist, the function inserts a new record for the measurement point and
    returns the newly inserted ID.

    :param db_conf: A dictionary containing the database configuration.
        It should have the following keys:
        - 'engine': Should be 'sqlite' for this function to work.
        - 'sqlite_path': The file path to the SQLite database directory.

    :param mp_name: The name of the measurement point.

    :param dt: The datetime object used to derive the SQLite file name from the configuration.

    :return: The ID of the measurement point. If the point does not exist, it is created and
             the new ID is returned.

    :raises Error: If any SQLite database errors occur during the query or insertion.

    **Example usage**::

        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/db/'
        }
        mp_name = 'Temperature'
        dt = datetime(2024, 12, 15)
        mp_id = sqlite_get_meas_point_id(db_conf, mp_name, dt)
    """
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
    """
    Inserts a new measurement and associated values into the SQLite database.

    This function inserts a new measurement record into the database, along with
    associated values, such as sensor values and their corresponding timestamps.
    It first retrieves or generates the necessary sensor and measurement point IDs,
    then creates a new measurement entry, and finally inserts the actual measurement
    values.

    :param db_conf: A dictionary containing the database configuration.
        It should have the following keys:
        - 'engine': Should be 'sqlite' for this function to work.
        - 'sqlite_path': The file path to the SQLite database directory.

    :param val_dict: A dictionary containing the measurement data to insert.
        It should have the following keys:
        - 'datetime': ISO formatted datetime string for the measurement timestamp.
        - 'meas_point': The name of the measurement point.
        - 'sensor_name': The name of the sensor.
        - 'max_val': The maximum allowed value for the sensor.
        - 'warn': The warning threshold for the sensor.
        - 'alarm': The alarm threshold for the sensor.
        - 'values': A list of sensor values to insert.

    :return: Always returns `False`. The return value is not used in this function.

    :raises ValueError: If the necessary database configuration or values are invalid.
    :raises sqlite3.Error: If any SQLite database errors occur during insertion.

    **Example usage**::

        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/db/'
        }
        val_dict = {
            'datetime': '2024-12-15T10:00:00',
            'meas_point': 'Temperature',
            'sensor_name': 'Sensor1',
            'tank_height': 120,
            'max_val': 100.0,
            'warn': 80.0,
            'alarm': 90.0,
            'values': [75.0, 76.0, 77.5]
        }
        result = insert_value(db_conf, val_dict)
    """

    meas_dt = datetime.fromisoformat(val_dict['datetime'])
    mp_id = sqlite_get_meas_point_id(db_conf, val_dict['meas_point'], meas_dt)
    s_id = sqlite_get_sensor_id(
        db_conf,
        mp_id,
        val_dict['sensor_name'],
        val_dict['tank_height'],
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
        return f"{dt.strftime('%m-%Y')}.sqlite"
    else:
        return False

def get_months_between(start_date, end_date):
    """
    Generate a list of months between two datetime objects in "%m-%Y" format.

    :param start_date: The start date.
    :type start_date: datetime

    :param end_date: The end date.
    :type end_date: datetime

    :returns: A list of strings representing the months in "%m-%Y" format.
    :rtype: list

    :raises ValueError: If `start_date` is later than `end_date`.

    **Example usage**::

        from datetime import datetime

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 5, 1)

        months = get_months_between(start_date, end_date)
        print(months)  # Output: ['01-2023', '02-2023', '03-2023', '04-2023', '05-2023']
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

def datetime_to_hours(x):
    output =x/3600.0
    return output

def convert_nan_to_none (x):
    try:
        if np.isnan(x):
            return None
    except TypeError:
        pass
    return x



def get_meas_data_from_sqlite_db(db_conf, dt_begin = None, dt_end = None):
    """
    Retrieve measurement data from SQLite database within a specified date range.

    This function is designed specifically for SQLite databases. It queries the data for a given
    date range (`dt_begin` to `dt_end`) and calculates additional metrics such as the slope and
    derivation of measurements. The results are returned as a pandas DataFrame.

    :param db_conf: Configuration dictionary containing database connection settings. Must include the key
        `engine` with value `'sqlite'` and `sqlite_path` specifying the path to the database files.
    :type db_conf: dict

    :param dt_begin: Start of the date range for the query. If not provided, defaults to 60 days before `dt_end`.
    :type dt_begin: datetime, optional

    :param dt_end: End of the date range for the query. If not provided, defaults to the current time in UTC.
    :type dt_end: datetime, optional

    :returns: A DataFrame containing the queried data with the following columns:
        - `mid`: Measurement ID
        - `dt`: Timestamp of the measurement
        - `mpName`: Measurement point name
        - `sensorId`: Sensor ID
        - `tank_height`: Height of the tank
        - `max_val`: Maximum value for the sensor
        - `warn`: Warning threshold
        - `alarm`: Alarm threshold
        - `meas_val`: Measured value
        - `slope`: Gradient of measured values over time
        - `derivation`: Derived metric calculated as `-slope / slope_date`
        - `value`: Difference between `tank_height` and `meas_val`, rounded to 1 decimal place
    :rtype: pd.DataFrame

    :raises ValueError: If the database engine is not SQLite, or if the inputs `dt_begin` or `dt_end` are
        not of type `datetime`, or if `dt_begin` is after `dt_end`.

    .. note::

        - The function splits the query by months and looks for SQLite files in the paths specified by
          `db_conf['sqlite_path']`.
        - Requires external helper functions:
            - `get_months_between(dt_begin, dt_end)` to determine months in the range.
            - `get_sqlite3_connection(db_path)` to establish SQLite connections.

    **Example usage**::

        from datetime import datetime

        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/sqlite/files'
        }
        dt_begin = datetime(2024, 1, 1)
        dt_end = datetime(2024, 2, 1)

        result = get_meas_data_from_sqlite_db(db_conf, dt_begin, dt_end)
        print(result.head())
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
        SELECT m.id,m.dt, mp.name, s.name, s.max_val, s.warn, s.alarm, AVG(v.value), tank_height
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
            if res.empty:
                continue
            res.columns = ['mid', 'dt', 'mpName', 'sensorId', 'max_val', 'warn', 'alarm', 'meas_val', 'tank_height']
            #res['value']
            for sens in res.sensorId.unique():
                res_sens = res[res['sensorId'] == sens].copy().reset_index(drop=True)
                try:
                    slope_val = pd.Series(np.gradient(res_sens.meas_val), name='slope')
                    #print (slope_val)

                    slope_date = pd.to_datetime(res_sens.dt)
                    slope_date = slope_date.astype('int64') // 10**9 / 3600 # in hours
                    slope_date = pd.Series(np.gradient(slope_date), name='slope')
                    #slope_date = slope_date.apply(datetime_to_hours)
                    res_sens['derivation'] = -slope_val / slope_date
                    if len (res_sens['derivation']) > 100:
                        res_sens['derivation_10'] = signal.savgol_filter(res_sens['derivation'], 10, 3)
                    else:
                        res_sens['derivation_10'] = 0.0
                except ValueError as e:
                    print (f"WARNING: Value Error: {e}")
                    res_sens['derivation'] = 0.0
                    res_sens['derivation_10'] = 0.0

                try:
                    inds = signal.find_peaks(res_sens['derivation'], height=10)[0]
                    inds_neg = signal.find_peaks(0-res_sens['derivation'], height=10)[0]
                    #print(inds)
                    res_sens['peaks_pos'] = np.nan
                    res_sens['peaks_neg'] = np.nan
                    res_sens.loc[inds, 'peaks_pos'] = res_sens['derivation_10'].iloc[inds]
                    res_sens.loc[inds_neg, 'peaks_neg'] = res_sens['derivation_10'].iloc[inds_neg]
                except ValueError as e:
                    print(f"Value Error:\t{e}")
                    res_sens['peaks_pos'] = np.nan
                    res_sens['peaks_neg'] = np.nan

                res_sens['peaks_pos'] = res_sens['peaks_pos'].replace({np.nan: None})
                res_sens['peaks_neg'] = res_sens['peaks_neg'].replace({np.nan: None})
                output = pd.concat([output, res_sens], ignore_index=True)
            conn.close()
        else:
            continue
    if 'max_val' in list(output.keys()) and 'meas_val' in list(output.keys()):
        output['value'] = round(output['tank_height'] - output['meas_val'], 1)
    #output['peaks_pos'] = output['peaks_pos'].apply(lambda x: None if np.isnan(x) else x)
    #output['peaks_neg'] = output['peaks_neg'].apply(lambda x: None if np.isnan(x) else x)
    #print(output['peaks_pos'].to_list())
    return output

def get_latest_database_file(path):
    """
        Retrieve the latest SQLite database file from a given directory based on its timestamp.

        This function searches the specified directory for files with the `.sqlite` extension, extracts
        the timestamp from the filename (in the format `MM-YYYY`), and identifies the most recent file.

        Args:
            path (str):
                The directory path containing the SQLite files.

        Returns:
            str:
                The filename of the most recent SQLite database, formatted as `MM-YYYY.sqlite`.

        Raises:
            ValueError: If no `.sqlite` files are found in the specified directory.

        **Example usage**::

            latest_file = get_latest_database_file('/path/to/sqlite/files')
            print(f"The latest database file is: {latest_file}")
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

def get_all_sqlite_files(path):
    """
    Retrieve all SQLite files from a specified directory, sorted by their date.

    This function scans the specified directory for files with a `.sqlite` extension,
    parses their filenames as dates in the format `MM-YYYY`, and returns a sorted list
    of filenames in the same format.

    :param path: The directory path to scan for SQLite files.
    :type path: str

    :returns: A list of filenames (`str`) with the `.sqlite` extension, sorted by their
              date in ascending order.
    :rtype: list

    :raises ValueError: If a file with a `.sqlite` extension does not conform to the `MM-YYYY` format.

    **Example usage**::

        Suppose the directory `/path/to/sqlite/` contains the following files:
        - `01-2024.sqlite`
        - `03-2023.sqlite`
        - `12-2023.sqlite`

        Calling the function:
        >>> sqlite_files = get_all_sqlite_files('/path/to/sqlite/')
        >>> print(sqlite_files)

        Would output:
        ['03-2023.sqlite', '12-2023.sqlite', '01-2024.sqlite']

    """

    datetime_list = []
    for file in os.listdir(path):
        if file.endswith(".sqlite"):
            datetime_list.append(
                datetime.strptime(
                    file.replace(".sqlite", ""),
                    "%m-%Y"
                )
            )
    return [x.strftime("%m-%Y.sqlite") for x in sorted(datetime_list)]

def assign_color(value, warn, alarm):
    if value < alarm:
        return 'alarm'
    elif value < warn:
        return 'warning'
    else:
        return 'normal'

def assign_sign(value,warn,alarm, dt):
    if dt < datetime.now(tz=pytz.utc) - timedelta(minutes=15):
        return '⚪'
    else:
        if value < alarm:
            return '🔴'
        elif value < warn:
            return '🟡'
        else:
            return '🟢'

def get_last_meas_data_from_sqlite_db(db_conf):
    """
    Retrieves the most recent measurement data from a SQLite database.

    This function connects to a SQLite database, executes an SQL query to fetch
    the latest measurement data for each sensor, and processes the results into
    a nested dictionary structure. The dictionary is organized by measurement
    point names and sensor names, and contains information about the measurement
    datetime, warning and alarm thresholds, maximum allowed values, and calculated
    values (the difference between the maximum value and the actual value).

    :param db_conf: A dictionary containing the database configuration.
        It should have the following keys:
        - 'engine': Should be 'sqlite' for this function to work.
        - 'sqlite_path': The file path to the SQLite database directory.

    :return: A nested dictionary structure with measurement data.
        The structure is as follows:
            output[measurement_point_name][sensor_name] = {
                'dt': datetime,           # Measurement timestamp
                'warn': warning_threshold,  # Warning threshold
                'alarm': alarm_threshold,  # Alarm threshold
                'tank_height': tank_height, # Height of the tank
                'max_val': max_value,      # Maximum allowed value for the sensor
                'value': calculated_value,  # Difference between tank_height and actual value
                'color': assigned_color    # Color assigned based on value and thresholds
            }

    :raises ValueError: If the 'engine' in db_conf is not 'sqlite'.

    :raises FileNotFoundError: If the SQLite database file does not exist.

    **Example usage**::

        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/db/'
        }

        result = get_last_meas_data_from_sqlite_db(db_conf)
    """

    if not db_conf['engine'] == 'sqlite':
        raise ValueError("Invalid Database function call: This functions is only for sqlite3 approach. Please configure it in your config.cfg file.")
    db_path_list = [db_conf['sqlite_path'] + x for x in get_all_sqlite_files(db_conf['sqlite_path'])]
    print (db_path_list)

    sql = """
        SELECT m.id, m.dt, mp.name, s.name, s.max_val, s.warn, s.alarm, AVG(v.value), tank_height
        FROM meas_val v
        INNER JOIN measurement m ON v.measurement_id = m.id
        INNER JOIN sensor s ON m.sensor_id = s.id
        INNER JOIN meas_point mp ON s.meas_point_id = mp.id
        WHERE m.id IN (
            SELECT id
            FROM measurement m_inner
            WHERE m_inner.dt = (
                SELECT MAX(m_inner2.dt)
                FROM measurement m_inner2
                WHERE m_inner2.sensor_id = m_inner.sensor_id
            )
        )
        GROUP BY m.dt;  
    """
    output = {}
    for db_path in db_path_list:
        if os.path.exists(db_path):
            conn, cur = get_sqlite3_connection(db_path)
            cur.execute(sql)
            res = cur.fetchall()
            #print (res)
            for row in res:
                if not row[2] in output:
                    output[row[2]] = {}
                output[row[2]][row[3]] = {}

                output[row[2]][row[3]]['dt'] = row[1]
                output[row[2]][row[3]]['warn'] = row[5]
                output[row[2]][row[3]]['alarm'] = row[6]
                output[row[2]][row[3]]['max_val'] = row[4]
                output[row[2]][row[3]]['tank_height'] = row[8]
                output[row[2]][row[3]]['value'] = round(row[8] - row[7],1)
                if row[1] < datetime.now(tz=pytz.utc) - timedelta(minutes=15):
                    output[row[2]][row[3]]['color'] = 'decrepated'
                else:
                    output[row[2]][row[3]]['color'] = assign_color(
                        output[row[2]][row[3]]['value'],
                        row[5],
                        row[6]
                    )
    return output

def get_available_meas_points_from_sqlite_db(db_conf):
    """
    Retrieve a list of available measurement points from SQLite databases.

    This function scans all SQLite database files in the specified path, executes a query
    to retrieve distinct measurement point names, and compiles them into a unique list.

    :param dict db_conf:
        A dictionary containing the database configuration.
        It must include the following keys:

        - ``engine`` (str): The database engine, which must be set to ``sqlite``.
        - ``sqlite_path`` (str): The directory path containing SQLite database files.

    :returns:
        A list of unique measurement point names.
    :rtype: list

    :raises ValueError:
        If the database engine specified in ``db_conf`` is not ``sqlite``.

    .. note::

        - The function uses ``get_all_sqlite_files`` to retrieve all SQLite database file names
          in the directory specified by ``db_conf['sqlite_path']``.
        - The function requires an external helper ``get_sqlite3_connection`` to establish SQLite
          connections.

    **Example usage**::

        db_conf = {
            'engine': 'sqlite',
            'sqlite_path': '/path/to/sqlite/files/'
        }
        measurement_points = get_available_meas_points_from_sqlite_db(db_conf)
        print(measurement_points)
    """
    if not db_conf['engine'] == 'sqlite':
        raise ValueError("Invalid Database function call: This functions is only for sqlite3 approach. Please configure it in your config.cfg file.")
    db_path_list = [db_conf['sqlite_path'] + x for x in get_all_sqlite_files(db_conf['sqlite_path'])]

    sql = "SELECT DISTINCT(name) FROM meas_point;"
    last_data = get_last_meas_data_from_sqlite_db(db_conf)

    output = {}
    for db_path in db_path_list:
        conn, cur = get_sqlite3_connection(db_path)
        cur.execute(sql)
        res = cur.fetchall()
        for row in res:
            if not row[0] in output:
                #output.append({
                #    "name":row[0],
                #    "status": [{'sensor':x, 'status':assign_sign(last_data[row[0]][x]['value'],last_data[row[0]][x]['warn'],last_data[row[0]][x]['alarm'])} for x in last_data[row[0]]]
                #})
                #o_str = f"{row[0]}".join([(f" {assign_sign(last_data[row[0]][x]['value'],last_data[row[0]][x]['warn'],last_data[row[0]][x]['alarm'])}") for x in last_data[row[0]]])
                output[row[0]] = [f" {assign_sign(last_data[row[0]][x]['value'],last_data[row[0]][x]['warn'],last_data[row[0]][x]['alarm'],last_data[row[0]][x]['value'])}" for x in last_data[row[0]]]

    return output

