# This script reads sensor configs from config.json and tests if sensors are available.
# If there is no calibration file, it offers to run a calibration run

import os.path
import json
import smbus2 as smbus
from WmPiUtils import read_pi_config_from_json
from WmSensors import Sensor


bus = smbus.SMBus(20)



config_file_pos = [os.path.abspath("../config.json"), os.path.abspath("../Pi/config.json"), os.path.abspath("./config.json")]
for c in config_file_pos:
    #print (os.path.abspath(c))
    if os.path.exists(c):
        config_file = c
        break

print(f"Wassermonitor2 sensor config script starting ...")
print(f"reading config from {config_file} ...")
config = read_pi_config_from_json(config_file)

for sensor in config['sensors']:
    print(f"\nTest sensor {sensor['name']}")
    s = Sensor(sensor, config["count_of_vals_per_meas"], configure=True)

