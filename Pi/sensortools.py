#Bibliotheken einbinden
import time
import datetime
import pymysql
#from mysqlopts import give_mysql_opts
import ast
import smbus2 as smbus
from time import sleep
import csv
from scipy.interpolate import interp1d

def get_raw_voltage (sensors,sensor):#sensor_position):
    """
    Reads and calculates the raw voltage from a specified sensor using the I2C bus.

    This function communicates with an I2C device at address `0x68` to set a standby
    configuration based on the provided sensor details. It then reads a block of data
    from the sensor, processes it, and returns the calculated voltage. If an error occurs,
    it returns `0`.

    Args:
        sensors (dict): A dictionary containing sensor configurations. Each key is a sensor
            identifier, and the value is a dictionary with configuration details.
            Example:
            {
                "sensor1": {"StBy": 128},
                "sensor2": {"StBy": 160}
            }
        sensor (str): The identifier of the sensor to read from, matching a key in the
            `sensors` dictionary.

    Returns:
        float: The calculated voltage from the sensor in volts. Returns `0` if an error occurs.

    Raises:
        None explicitly, but generic exceptions are caught and handled within the function.

    Notes:
        - The function assumes the I2C device is connected to bus `1`.
        - The voltage calculation is based on a 12-bit ADC (resolution of 4096).
        - The standby mode (`StBy`) value is retrieved from the `sensors` dictionary for
          the specified sensor.
    """
    bus = smbus.SMBus(1)#Bus definieren
    addr = 0x68

    try:
        stBy = sensors[sensor]["StBy"]

        bus.write_byte(addr,stBy)
        sleep(1)
        var = bus.read_i2c_block_data(addr,0,3)
        var = var[0]*256 + var[1]
        voltage = 20/4096*var

        return voltage
    except:
        return 0


def get_calib_value (sensors, sensor):
    """
    Reads and interpolates the calibrated value for a specified sensor.

    This function retrieves calibration data for the specified sensor from a CSV file,
    reads the current raw voltage value from the sensor, and interpolates it against the
    calibration data to calculate the calibrated value. If an error occurs during the
    interpolation, it returns `0`.

    Args:
        sensors (dict): A dictionary containing sensor configurations. Each key is a sensor
            identifier, and the value is a dictionary with details, including an "id" field
            used to locate the sensor's calibration file.
            Example:
            {
                "sensor1": {"id": "1"},
                "sensor2": {"id": "2"}
            }
        sensor (str): The identifier of the sensor to read from, matching a key in the
            `sensors` dictionary.

    Returns:
        float: The interpolated calibrated value for the sensor. Returns `0` if an error occurs.

    Notes:
        - The calibration data is stored in a CSV file named `calib_date_sensor_<id>.csv`,
          where `<id>` corresponds to the `id` field of the sensor in the `sensors` dictionary.
        - The CSV file is expected to have two semicolon-separated columns:
          - Column 0: `y` values (e.g., physical values such as temperature).
          - Column 1: `x` values (e.g., raw voltage).
        - The calibration process uses linear interpolation with `scipy.interpolate.interp1d`.
        - The function depends on `get_raw_voltage` to read the current raw voltage.

    Raises:
        None explicitly, but exceptions during interpolation are caught and handled within
        the function.

    Example:
        sensors = {
            "sensor1": {"id": "001"},
            "sensor2": {"id": "002"}
        }
        value = get_calib_value(sensors, "sensor1")
        print(value)
    """

    calib_data = dict()
    f = 'calib_date_sensor_%s.csv'%sensors[sensor]["id"]
    calib_data["x"] = list()
    calib_data["y"] = list()

    
    with open(f) as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            #print (row)
            calib_data["x"].append(float(row[1]))
            calib_data["y"].append(float(row[0]))


    x_value = get_raw_voltage(sensors,sensor)

    calib = interp1d(calib_data["x"],calib_data["y"])
    try:
        calib_value = calib(x_value)
    except:
        calib_value = 0

    return calib_value

