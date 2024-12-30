"""
Data Crawler
============

This script is a data crawler designed to:
1. Create sensor instances from a configuration file.
2. Retrieve measurement values from the sensors.
3. Store the measurement values in temporary storage.
4. Continuously repeat the process at defined intervals.
"""

import os.path
import json
from WmPiUtils import read_pi_config_from_json
from WmSensors import Sensor
from time import sleep
from datetime import datetime


config_file_pos = [os.path.abspath("../config.json"), os.path.abspath("../Pi/config.json"), os.path.abspath("./config.json")]
for c in config_file_pos:
    #print (os.path.abspath(c))
    if os.path.exists(c):
        config_file = c
        break

print(f"Wassermonitor2 datacrawler starting at {datetime.now()} ...")
print(f"reading config from {config_file} ...")
config = read_pi_config_from_json(config_file)

def get_sensors_from_config():
    """
    Create sensor instances from the configuration file.

    This function reads the sensor configuration and initializes sensor objects.

    :return: A list of initialized sensor objects.
    :rtype: list[Sensor]
    """

    sensors = []
    for s in config["sensors"]:
        sensors.append(Sensor(s, config["count_of_vals_per_meas"]))
    return sensors
# Get Sensor values


def save_values_to_temp_storage(s, vals, now):
    """
    Save measurement values to temporary storage.

    This function saves the measurement data for a sensor in a JSON file in the
    specified temporary storage directory.

    :param s: The sensor object.
    :type s: Sensor
    :param vals: The measurement values.
    :type vals: list
    :param now: The timestamp of the measurement.
    :type now: datetime.datetime
    """

    path = os.path.abspath(config['temp_storage_path'])
    if not os.path.exists(path):
        print (f"\ttemporary storage path not found.\n\t{path}\n\t  creating... ")
        os.makedirs(path)

    filename = f"{now.isoformat()}_{s.name}.json"
    filename = f"{path}/{filename}"
    data = {
        "sensor": s.name,
        "dt": now.isoformat(),
        "values": vals,
    }
    with open (filename, 'w', encoding='utf-8') as f:
        json.dump(data,f, ensure_ascii=False, indent=4)


def measurement():
    """
    Perform a measurement for all sensors and save the results.

    This function iterates over all sensors, retrieves measurement values, and
    saves the values to temporary storage with a timestamp.
    """

    for s in sensors:
        now = datetime.now()
        vals = s.perform_measurement()
        save_values_to_temp_storage(s, vals, now)



if __name__ == "__main__":
    """
    Main execution loop.

    This script initializes sensors from the configuration, then enters a loop where
    it performs measurements and saves the results at intervals defined in the configuration.
    """

    sensors = get_sensors_from_config()
    while True:
        measurement()
        sleep(config["meas_interval"])


