"""
Sensor Module
=============

This module contains the base class `Sensor` and the specialized class `IFM_O1`
for interacting with different sensors, including configuration, calibration, and I2C communication.
"""

from time import sleep
import smbus2 as smbus
import csv
import os
from scipy.interpolate import interp1d

class Sensor():
    """
    Base class for sensors.

    This class serves as a foundation for specialized sensor classes and provides
    common methods and attributes.

    :param sensor_dict: A dictionary containing the sensor configuration.
    :type sensor_dict: dict
    :param cnt_of_vals_per_meas: The number of values per measurement.
    :type cnt_of_vals_per_meas: int
    """
    def __new__(cls, sensor_dict, cnt_of_vals_per_meas):
        """
        Factory method for dynamically selecting the sensor class based on its type.

        :param sensor_dict: A dictionary containing the sensor configuration.
        :type sensor_dict: dict
        :param cnt_of_vals_per_meas: The number of values per measurement.
        :type cnt_of_vals_per_meas: int
        :return: An instance of the appropriate sensor subclass.
        :rtype: Sensor
        :raises ValueError: If the sensor type is unknown.
        """
        sensor_classes = {
            "IFM_O1": IFM_O1
        }
        if sensor_dict["type"] not in sensor_classes:
            raise ValueError(f"Unknown sensor type: {sensor_dict['type']}")

        sensor_class = sensor_classes[sensor_dict["type"]]
        instance = super().__new__(sensor_class)
        return instance

    def __init__(self, sensor_dict, cnt_of_vals_per_meas):
        """
        Initialize common sensor attributes.

        :param sensor_dict: A dictionary containing the sensor configuration.
        :type sensor_dict: dict
        :param cnt_of_vals_per_meas: The number of values per measurement.
        :type cnt_of_vals_per_meas: int
        """
        self.name = sensor_dict["name"]
        self.calib_file = os.path.abspath(sensor_dict["calib_file"])
        self.sensor_offset_zero = float(sensor_dict["tank_height"])
        self.max_val = float(sensor_dict["max_val"])
        self.warn = float(sensor_dict["warn"])
        self.alarm = float(sensor_dict["alarm"])
        self.cnt_of_vals_per_meas = cnt_of_vals_per_meas
    def calibrate_data(self, raw_data):
        """
        Calibrate raw data into meaningful values.

        This method must be implemented in the dedicated sensor subclass.

        :param raw_data: The raw data to be calibrated.
        :type raw_data: any
        :raises NotImplementedError: If the method is not implemented in the subclass.
        """
        raise NotImplementedError("This Method has to be defined in the dedicated sensor class (e.g. IFM_O1()")

    def get_full_sensor_config(self):
        """
        Retrieve the full configuration of the sensor.

        This method must be implemented in the dedicated sensor subclass.

        :raises NotImplementedError: If the method is not implemented in the subclass.
        """
        raise NotImplementedError("This Method has to be defined in the dedicated sensor class (e.g. IFM_O1()")

    def perform_measurement(self):
        """
        Perform a measurement for the sensor.

        This method must be implemented in the dedicated sensor subclass.

        :raises NotImplementedError: If the method is not implemented in the subclass.
        """

        raise NotImplementedError("This Method has to be defined in the dedicated sensor class (e.g. IFM_O1()")

class IFM_O1(Sensor):
    """
    Specialized class for the IFM_O1 sensor.

    :param sensor_dict: A dictionary containing the sensor configuration.
    :type sensor_dict: dict
    :param cnt_of_vals_per_meas: The number of values per measurement.
    :type cnt_of_vals_per_meas: int
    """

    def __init__(self, sensor_dict, cnt_of_vals_per_meas):
        """
        Initialize the IFM_O1 sensor attributes.

        :param sensor_dict: A dictionary containing the sensor configuration.
        :type sensor_dict: dict
        :param cnt_of_vals_per_meas: The number of values per measurement.
        :type cnt_of_vals_per_meas: int
        """

        super().__init__(sensor_dict, cnt_of_vals_per_meas)

        self.i2c_addr = sensor_dict["i2c"]["addr"]
        self.i2c_name = sensor_dict["i2c"]["name"]
        self.i2c_id = sensor_dict["i2c"]["id"]
        self.i2c_StBy = sensor_dict["i2c"]["StBy"]
        self.calib_data = self.get_calib_data()


    def get_i2c_address(self):
        """
        Get the I2C address and related information for the sensor.

        :return: A formatted string with I2C information.
        :rtype: str
        """
        return f"#### I2C Address for sensor {self.name} ####\n\taddr:{self.i2c_addr}\n\tname:{self.i2c_name}\tid:{self.i2c_id}\tStBy:{self.i2c_StBy}"

    def get_full_sensor_config(self):
        """
        Retrieve the full configuration of the IFM_O1 sensor.

        :return: A formatted string with the sensor configuration.
        :rtype: str
        """

        return f"""
            #### Full sensor config for sensor {self.name} ####
            \tname: {self.name}
            \tcalibration file: {self.calib_file}
            \tsensor_offset_zero: {self.sensor_offset_zero}
            \tmax_val: {self.max_val}
            \twarn: {self.warn}
            \talarm: {self.alarm}
            \tcnt_of_sensors_per_meas: {self.cnt_of_vals_per_meas}
            \ti2c config:
            \t\tname:{self.i2c_name}
            \t\taddr:{self.i2c_addr}
            \t\tid:{self.i2c_id}
            \t\tStBy:{self.i2c_StBy}          
        """
    def get_raw_voltage(self):
        """
        Retrieve the raw voltage from the sensor via I2C.

        :return: The raw voltage value.
        :rtype: float
        :raises Exception: If an error occurs during I2C communication.
        """
        bus = smbus.SMBus(1)

        try:
            bus.write_byte(self.i2c_addr, self.i2c_StBy)
            sleep(1)
            var = bus.read_i2c_block_data(self.i2c_addr, 0, 3)
            var = var[0] * 256 + var[1]
            voltage = 20 / 4096 * var
            return voltage
        except Exception as e:
            print (f"\tget_raw_voltage: ERROR occurred:\n\t\t{e}")

    def get_calib_data(self):
        """
        Retrieve calibration data from the calibration file.

        :return: A dictionary with calibration data (`x` and `y` values).
        :rtype: dict
        """
        cd = {
            "x": [],
            "y": []
        }

        if not os.path.exists(self.calib_file):
            raise FileNotFoundError(f"ERROR: No calibration file {self.calib_file} found. Please create one using ./calib.py (Please see readme file...).")

        with open(self.calib_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            for row in reader:
                # print (row)
                cd["x"].append(float(row[1]))
                cd["y"].append(float(row[0]))

        return cd

    def get_calib_value(self):
        """
        Get the calibrated value by interpolating raw data.

        :return: The calibrated value.
        :rtype: float
        :raises Exception: If an error occurs during calibration.
        """
        try:
            raw_value = self.get_raw_voltage()
            #distance = raw_value * 100
            calib = interp1d(self.calib_data["x"], self.calib_data["y"])
            calib_value = calib(raw_value)
            return calib_value
        except Exception as e:
            print(f"\tWARNING get_calib_voltage: No data occurred:\n\t\t{e}")
            return 0.0

    def perform_measurement(self):
        """
        Perform a series of measurements for the sensor.

        :return: A list of calibrated values from the measurements.
        :rtype: list[float]
        """
        output = []
        for i in range(self.cnt_of_vals_per_meas):
            print (f"performing measurement {i} for sensor {self.name} ...")
            output.append(self.get_calib_value())
            sleep(1)
        return output