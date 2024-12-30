"""
Utility Module: Raspberry Pi Configuration
==========================================

This module provides utility functions for reading configuration data for Raspberry Pi from JSON files.
"""

import json
import os

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
