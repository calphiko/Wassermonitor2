"""
This script processes measurement data stored in temporary storage, signs it, and sends it to a specified API.

Steps:
1. Read data from temporary storage.
2. Build a full payload.
3. Sign the data.
4. Send a request to the API.

Configuration:
The script reads configuration settings from a `config.json` file located in predefined paths.

Modules:
- `psk_sign`: Used for signing data with a private RSA key.
- `WmPiUtils`: Utility functions for reading configuration files.

Dependencies:
- `requests`: For sending HTTP POST requests to the API.
- `json`, `os`, `glob`, `datetime`: Standard libraries for file handling and processing.
"""

from psk_sign import sign_meas_data
from WmPiUtils import read_pi_config_from_json
from datetime import datetime
import os
import glob
import json
from requests import post

config_file_pos = [os.path.abspath("../config.json"), os.path.abspath("../Pi/config.json"), os.path.abspath("./config.json")]
for c in config_file_pos:
    if os.path.exists(c):
        config_file = c
        break

config = read_pi_config_from_json(config_file)


def read_json(filename):
    """
    Read a JSON file and return its contents as a Python dictionary.

    :param filename: Path to the JSON file.
    :type filename: str
    :return: Parsed JSON data.
    :rtype: dict
    """

    with open (filename, 'r') as f:
        d = json.load(f)
    return d


def list_files_from_storage():
    """
    List all JSON files in the temporary storage directory.

    :return: List of file paths to JSON files in the temporary storage.
    :rtype: list[str]
    """

    return glob.glob(f"{os.path.abspath(config['temp_storage_path'])}/*.json")


def build_payload(meas_file):
    """
    Build the payload (pl) by reading, augmenting, and signing measurement data.

    :param meas_file: Path to the measurement JSON file.
    :type meas_file: str
    :return: Signed payload containing measurement data.
    :rtype: dict
    """

    data = read_json(meas)
    data['meas_point'] = config['name']

    pl = sign_meas_data(f"{os.path.abspath(config['psk_path'])}/private_key.pem", data)

    # return full payload
    return pl


def send_payload(pl):
    """
    Send the signed payload to the API.

    :param pl: The signed measurement payload.
    :type pl: dict
    :return: Response object from the HTTP POST request.
    :rtype: requests.Response
    """

    headers = {
        "Authorization": f"Bearer {config['token']}"
    }
    r = post(f"{config['api_url']}/insert/", json=json.dumps(pl), headers=headers)
    return r


if __name__ == '__main__':
    """
    Main execution flow:
    - List all measurement files in temporary storage.
    - Build and sign a payload for each file.
    - Send the payload to the API.
    - If successful, remove the processed file; otherwise, log an error.
    """

    for meas in list_files_from_storage():
        payload = build_payload(meas)
        print(f"Send data from '{payload['data']['sensor_name']}' at {datetime.fromisoformat(payload['data']['datetime']).strftime('%Y-%m-%d %H:%M:%S')} to API...")
        r = send_payload(payload)

        if r.status_code == 200:
            print (f"\tstatus code: {r.status_code}")
            os.remove(meas)
        else:
            print (f"\tERROR: Data not send\n\t\tStatus code: {r.status_code} {r.text}")
