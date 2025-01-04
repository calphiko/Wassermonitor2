"""
Module for handling SSH-style public key verification and loading authorized keys.

This module provides functions to load authorized SSH public keys from a specified
file and to verify signatures using RSA with PSS padding and SHA-256 hashing.

**Functions**:
    - :func:`load_authorized_keys`: Loads authorized SSH public keys from a file.
    - :func:`verify_signature`: Verifies the signature of the data using the provided public key.
"""

import os.path

from cryptography.hazmat.primitives.serialization import load_ssh_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

import json


def load_authorized_keys(file_path):
    """
    Loads a list of authorized SSH public keys from a file and returns them in a dictionary.

    The function reads the given file, processes each line, and extracts the public keys.
    The public keys are stored in a dictionary, where the keys are the comments associated
    with each key and the values are the actual RSA public key objects.

    :param file_path: The path to the file containing the SSH public keys.

    :return: A dictionary where the keys are the comments (client IDs) and the values are
             the RSA public keys corresponding to each client.

    **Example usage**::

        authorized_keys = load_authorized_keys("/path/to/authorized_keys.txt")
    """
    authorized_keys = {}
    if not os.path.exists(file_path):
        print ("WARNING: Authorized Key File not found. Please create and add you meas-points public-keys.")
    else:
        with open(file_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        key_data = parts[1]
                        comment = parts[2] if len(parts) > 2 else None
                        try:
                            public_key = load_ssh_public_key(
                                f"ssh-rsa {key_data}".encode(),
                                backend=default_backend()
                            )
                            authorized_keys[comment] = public_key
                        except Exception as e:
                            print(f"Error loading key for {comment}: {e}")
    return authorized_keys


def verify_signature (public_key, data, signature):
    """
    Verifies the signature of the given data using the provided public key.

    This function checks whether the provided signature matches the data when signed by
    the corresponding private key. It uses RSA with PSS padding and SHA-256 hashing.

    **Args**:
        public_key (RSAPublicKey): The public key to verify the signature with.
        data (dict): The original data that was signed.
        signature (str): The base64 encoded signature to verify.

    **Returns**:
        bool: True if the signature is valid, raises an exception otherwise.

    **Raises**:
        ValueError: If the signature is invalid.

    **Example**::

        try:
            verify_signature(public_key, data, signature)
        except ValueError:
            print("Invalid signature")
    """
    try:
        public_key.verify(
            signature,
            json.dumps(data).encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        raise ValueError("Invalid signature") from e



