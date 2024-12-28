from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import json
import os

config_json_path = './config.json'

def read_config_json():
    with open(config_json_path) as f:
        d = json.load(f)
    return d["psk_path"], d["name"]

def create_psk_path_if_not_exists(psk_path):
    if not os.path.exists(psk_path):
        os.makedirs(psk_path)
        print (f"\t {psk_path} created")

def generate_key_pair(psk_path, key_size=2048):
    # Private Key erstellen
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )

    # Private Key speichern
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(f"{psk_path}/private_key.pem", "wb") as f:
        f.write(private_pem)

    # Public Key speichern
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(f"{psk_path}/public_key.pem", "wb") as f:
        f.write(public_pem)

    print("Keys generated and saved as 'private_key.pem' and 'public_key.pem'.")


def convert_to_ssh_format(public_key_path, name ):
    with open(f"{public_key_path}/public_key.pem", "rb") as f:
        public_key = load_pem_public_key(f.read())

    ssh_key = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode("utf-8")

    print("SSH Public Key Format:")
    print(f"{ssh_key} {name}")


psk_path,name  = read_config_json()
create_psk_path_if_not_exists(psk_path)
generate_key_pair(psk_path)
convert_to_ssh_format(psk_path, name)
