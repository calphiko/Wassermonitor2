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
import termplotlib as tmpl
from scipy.interpolate import interp1d
import WmPiUtils

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
    def __new__(cls, sensor_dict, cnt_of_vals_per_meas, configure = False):
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

    def __init__(self, sensor_dict, cnt_of_vals_per_meas, config_file = "./config.json", configure = False):
        """
        Initialize common sensor attributes.

        :param sensor_dict: A dictionary containing the sensor configuration.
        :type sensor_dict: dict
        :param cnt_of_vals_per_meas: The number of values per measurement.
        :type cnt_of_vals_per_meas: int
        """
        self.name = sensor_dict["name"]
        self.type = sensor_dict["type"]
        self.calib_file = os.path.abspath(sensor_dict["calib_file"])
        self.sensor_offset_zero = float(sensor_dict["tank_height"])
        self.max_val = float(sensor_dict["max_val"])
        self.warn = float(sensor_dict["warn"])
        self.alarm = float(sensor_dict["alarm"])
        self.config_file = os.path.abspath(config_file)
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

    def __init__(self, sensor_dict, cnt_of_vals_per_meas = 5, configure = False):
        """
        Initialize the IFM_O1 sensor attributes. If no calibration file is found, it can be created or replaced by a default one

        :param sensor_dict: A dictionary containing the sensor configuration.
        :type sensor_dict: dict
        :param cnt_of_vals_per_meas: The number of values per measurement.
        :type cnt_of_vals_per_meas: int (default 5)
        :param configure: Should ask for configration scripts
        :type configure: bool (default False)
        """

        super().__init__(sensor_dict, cnt_of_vals_per_meas)
        self.i2c_addr = int(sensor_dict["i2c"]["addr"], 16)
        self.i2c_device = sensor_dict["i2c"]["i2c_device"]
        self.i2c_StBy = 128 + int(sensor_dict["i2c"]["adc_channel"])*32
        try:
            self.calib_data = self.get_calib_data()
        except FileNotFoundError:
            q_create_calib = str()
            if configure:
                while (q_create_calib == str()):
                    q_create_calib=input (f"\tNo calibration file found for Sensor {self.name}. \n\tShould we create one (you will need a calibration setup for this). \n\tOtherwise we can use a default calibration file, but here, the measured value will be inaccurate or wrong. \n\tPress 'y' for creating a new file (default no)! " or "n")
                    if q_create_calib == "y":
                        self.create_calibration_file()
                    elif q_create_calib == "n" or q_create_calib == "no" or q_create_calib == "":
                        q_create_calib = "n"
                        print (f"\tWARNING: {self.name} uses the default calibration file. The values will be incorrect or inaccurate")
                        self.calib_file = os.path.abspath("./calib_date_sensor.tmpl")
                    else:
                        print ("please type 'y' or 'n'")

                # TERM PLOT
                cd = {
                    "x":[],
                    "y":[]
                }
                with open(self.calib_file, 'r') as csvfile:
                    reader = csv.reader(csvfile, delimiter=";")
                    for row in reader:
                        # print (row)
                        cd["x"].append(float(row[1]))
                        cd["y"].append(float(row[0]))
                fig = tmpl.figure()
                fig.plot(cd["x"], cd["y"])
                fig.show()
            else:
                print(f"\tWARNING: {self.name} uses the default calibration file. The values will be incorrect or inaccurate")
                self.calib_file = os.path.abspath("./calib_date_sensor.tmpl")

            self.calib_data = self.get_calib_data()

        self.test_connection()

    def create_calibration_file(self):
        """
        Create a calibration file for a sensor.

        This function guides the user through the creation of a calibration file for a sensor.
        The calibration involves measuring raw sensor output at predefined distances and saving
        the results to a CSV file. If a calibration file already exists, the user is prompted to
        confirm overwriting it. Once created, the calibration file path is saved to the sensor's
        configuration.

        :return: True if the calibration file is successfully created, False if the process is aborted.
        :rtype: bool
        :raises FileNotFoundError: If the specified configuration file does not exist.
        :raises OSError: If there is an error during file operations (e.g., permissions issues).
        :raises ValueError: If invalid user input is provided during overwrite confirmation.
        """

        CALIB_DIST = [17, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
        print(f"\n\tcreating calibration file.... (from {CALIB_DIST[0]} cm to {CALIB_DIST[-1]} cm)")

        if os.path.isdir(self.calib_file):
            self.calib_file = f"{self.calib_file}/calib_file_{self.name}.csv"

        if os.path.exists(self.calib_file):
            overwrite = str()
            while overwrite == str:
                overwrite = input(f"\tCalibration file\n\t\t{self.calib_file}\n\texists. Are you sure to overwrite (n): " or "n")
                if overwrite == "n" or overwrite == "no":
                    print ("Aborting...")
                    return False
                elif overwrite == "y" or overwrite =="yes":
                    overwrite = "y"
                else:
                    print("please type 'y' or 'n'")
                    overwrite = str()

        print (f"\n\tSTARTING SENSOR CALIBRATION FOR SENSOR {self.name}\n\tSaving calibration data to {self.calib_file}")
        with open(self.calib_file, 'w') as f:
            for d in CALIB_DIST:
                input(f"\t\tSet sensor to {d} cm distance and press ENTER")
                d_m = self.get_raw_voltage()
                f.write(f"{d};{d_m}\n")
                print (f"\t\t\t{d_m}")


        # DON'T FORGET TO WRITE CALIB FILE TO CONFIG
        c_dict = WmPiUtils.read_pi_config_from_json(self.config_file)
        for i in range(len(c_dict["sensors"])):
            if c_dict["sensors"][i]["name"] == self.name:
                c_dict["sensors"][i]["calib_file"] = self.calib_file
        WmPiUtils.update_pi_config_from_dict(c_dict, self.config_file)
        return

    def test_connection(self):
        """
       Test the connection to the sensor.

       This function checks whether the sensor is properly connected by attempting to read its raw voltage.
       If the connection is successful, it returns `True`. Otherwise, it prints a warning and returns `False`.

       :return: True if the sensor connection is successful, False if the connection fails.
       :rtype: bool
       :raises ConnectionError: If the sensor cannot be reached or is not connected.
       """

        try:
            self.get_raw_voltage()
            return True
        except ConnectionError as e:
            print (f"\tWARNING: sensor {self.name} has no connection.")
            return False

    def get_i2c_address(self):
        """
        Get the I2C address and related information for the sensor.

        :return: A formatted string with I2C information.
        :rtype: str
        """
        return f"#### I2C Address for sensor {self.name} ####\n\ti2c_device:{self.i2c_device}\n\taddr:{self.i2c_addr}\n\tStBy:{self.i2c_StBy}"

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

        if not os.path.isfile(self.calib_file):
            raise FileNotFoundError(f"ERROR: The path in '{self.calib_file}' is a directory. Please specify a calibration file!")

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
            calib_value = float(calib(raw_value))
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
