from psk_sign import sign_meas_data
from WmPiUtils import read_pi_config_from_json
import os

config_file_pos = [os.path.abspath("../config.json"), os.path.abspath("../Pi/config.json"), os.path.abspath("./config.json")]
for c in config_file_pos:
    #print (os.path.abspath(c))
    if os.path.exists(c):
        config_file = c
        break
config = read_pi_config_from_json(config_file)

# 1. read data from temporary storage
# 2. build full payload
# 3. sign data
# 4. request to api