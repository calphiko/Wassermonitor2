"""
Key Management Script
=====================

This script provides functionality for managing public and private key pairs. It includes:
1. Reading configuration data from a JSON file.
2. Creating a directory for storing pre-shared keys (PSK) if it does not exist.
3. Generating RSA key pairs and saving them to the specified PSK directory.
4. Converting the public key to SSH format for usage in authorized keys files.

Dependencies:
- `cryptography.hazmat`: Provides cryptographic primitives for generating and handling keys.
- `json`: For reading configuration data from JSON files.
- `os`: For handling file paths and directories.

"""


from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import json
import os

config_file_pos = [os.path.abspath("../config.json"), os.path.abspath("../Pi/config.json"), os.path.abspath("./config.json")]
for c in config_file_pos:
    #print (os.path.abspath(c))
    if os.path.exists(c):
        config_file = c
        break
config_json_path = config_file

def read_config_json():
    """
    Read configuration data from the JSON file.

    This function reads the PSK path and name from the configuration file.

    :return: A tuple containing the PSK path and name.
    :rtype: tuple[str, str]
    :raises FileNotFoundError: If the configuration file does not exist.
    :raises json.JSONDecodeError: If the configuration file is not valid JSON.
    """

    with open(config_json_path) as f:
        d = json.load(f)
    return d["psk_path"], d["name"]

def create_psk_path_if_not_exists(psk_path):
    """
    Create the PSK directory if it does not already exist.

    :param psk_path: The path where the PSK directory should be created.
    :type psk_path: str
    """

    if not os.path.exists(psk_path):
        os.makedirs(psk_path)
        print (f"\t {psk_path} created")

def generate_key_pair(psk_path, key_size=2048):
    """
    Generate an RSA key pair and save them to the PSK directory.

    The private key is saved as `private_key.pem`, and the public key as `public_key.pem`.

    :param psk_path: The directory where the keys will be saved.
    :type psk_path: str
    :param key_size: The size of the RSA key in bits. Default is 2048.
    :type key_size: int
    """

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )


    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(f"{psk_path}/private_key.pem", "wb") as f:
        f.write(private_pem)


    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(f"{psk_path}/public_key.pem", "wb") as f:
        f.write(public_pem)

    print("Keys generated and saved as 'private_key.pem' and 'public_key.pem'.")


def convert_to_ssh_format(public_key_path, name ):
    """
    Convert the public key to SSH format.

    This function reads the public key and converts it to OpenSSH format, appending the provided name.

    :param public_key_path: The directory containing the `public_key.pem` file.
    :type public_key_path: str
    :param name: The name to append to the SSH public key.
    :type name: str
    """

    with open(f"{public_key_path}/public_key.pem", "rb") as f:
        public_key = load_pem_public_key(f.read())

    ssh_key = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode("utf-8")

    print("SSH Public Key Format (please copy to your servers authorized_keys file for enabling sending data to the API:")
    print(f"{ssh_key} {name}")

    with open(f"{public_key_path}/public_key.rsa", 'w') as f:
        f.write(f"{ssh_key} {name}")

if __name__ == "__main__":
    psk_path,name = read_config_json()
    create_psk_path_if_not_exists(psk_path)
    generate_key_pair(psk_path)
    convert_to_ssh_format(psk_path, name)
