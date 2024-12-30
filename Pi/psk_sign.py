"""
Digital Signature Module
========================

This module provides functionality for signing measurement data using a private RSA key.
It includes functions to load a private key from a file and to generate a digital signature
for a given dataset.
"""

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
import json

def get_priv_key_from_file(file_path):
    """
    Load a private key from a PEM file.

    This function reads a PEM-encoded private key from a specified file and loads it into memory.

    :param file_path: The path to the PEM file containing the private key.
    :type file_path: str
    :return: The loaded private key.
    :rtype: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey
    :raises ValueError: If the file is not a valid PEM private key file.
    :raises TypeError: If the key format is unsupported.
    :raises Exception: For other errors during key loading.
    """
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None  # Falls der Schlüssel passwortgeschützt ist, gib hier das Passwort an.
        )
    return private_key

def sign_meas_data(priv_key_file, data):
    """
    Sign measurement data using a private RSA key.

    This function generates a digital signature for the given data using a private key loaded
    from the specified file. The data and its corresponding signature are returned as a dictionary.

    :param priv_key_file: The path to the PEM file containing the private RSA key.
    :type priv_key_file: str
    :param data: The measurement data to be signed. It must be serializable to JSON.
    :type data: dict
    :return: A dictionary containing the original data and the signature in hexadecimal format.
    :rtype: dict
    :raises ValueError: If the private key file is invalid or if the data is not serializable to JSON.
    :raises TypeError: If the key or data format is incorrect.
    :raises Exception: For other errors during signing.
    """
    private_key = get_priv_key_from_file(priv_key_file)
    message = json.dumps(data).encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

    payload = {
        "data": data,
        "signature": signature.hex()
    }
    return payload