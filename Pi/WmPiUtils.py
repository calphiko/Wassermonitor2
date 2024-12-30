import json
import os

def read_pi_config_from_json(json_file):
    json_abs_path = os.path.abspath(json_file)
    with open(json_abs_path, 'r') as f:
        d = json.load(f)

    return d
