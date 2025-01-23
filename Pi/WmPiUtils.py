"""
Utility Module: Raspberry Pi Configuration
==========================================

This module provides utility functions for reading configuration data for Raspberry Pi from JSON files.
"""

import json
import os
import shutil

def read_pi_config_from_json(json_file):
    """
    Read and parse the Raspberry Pi configuration from a JSON file.

    This function reads a JSON file containing configuration data, parses it, and returns the resulting dictionary.

    :param json_file: The path to the JSON configuration file.
    :type json_file: str
    :return: A dictionary containing the parsed configuration data.
    :rtype: dict
    :raises FileNotFoundError: If the specified JSON file does not exist.
    :raises json.JSONDecodeError: If the file is not a valid JSON.
    """

    json_abs_path = os.path.abspath(json_file)
    with open(json_abs_path, 'r') as f:
        d = json.load(f)

    return d

def update_pi_config_from_dict(config_dict, json_file):
    """
    Update the Raspberry Pi configuration file using the provided dictionary.

    This function updates a JSON configuration file with the contents of the given dictionary.
    If the file already exists, a backup of the original file is created before overwriting it.

    :param config_dict: A dictionary containing the configuration data to be written.
    :type config_dict: dict
    :param json_file: The path to the JSON configuration file to be updated.
    :type json_file: str
    :return: None
    :rtype: NoneType
    :raises FileNotFoundError: If the specified path to save the backup or JSON file is invalid.
    :raises OSError: If there is an error during file operations (e.g., permissions issues).
    """

    json_abs_path = os.path.abspath(json_file)

    # BACKUP OLD FILE
    if os.path.exists(json_abs_path):
        shutil.copyfile(json_abs_path, f"{json_abs_path}.bak")

    # WRITE NEW FILE
    with open(json_abs_path, 'w') as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=4)
        return

