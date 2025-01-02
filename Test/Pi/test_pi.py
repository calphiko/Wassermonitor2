# Testsuite for Pi part
import os.path
from datetime import datetime
import sys
sys.path.append("../../Pi")

from Pi import WmPiUtils as WmPU
from Pi.WmSensors import Sensor
import unittest

config_dict = WmPU.read_pi_config_from_json(os.path.abspath("config.json"))
config_dict["sensors"][0]["calib_file"] = os.path.abspath(f"{config_dict['sensors'][0]['calib_file']}")
config_dict["sensors"][1]["calib_file"] = os.path.abspath(f"{config_dict['sensors'][1]['calib_file']}")

class Test_Pi(unittest.TestCase):
    def test_sensor_initialization(self):
        for s in config_dict["sensors"]:
            sensor = Sensor(s, config_dict["count_of_vals_per_meas"])
            print (sensor.get_full_sensor_config())

if __name__ == '__main__':
    unittest.main()