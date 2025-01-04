# WARNING BOT MAIN FILE

import os
from datetime import datetime
import configparser
import json
from requests import post

config_file = str()
config_file_pos = [os.path.abspath("../config.cfg"), os.path.abspath("../Server/config.cfg")]
for c in config_file_pos:
    print (os.path.abspath(c))
    if os.path.exists(c):
        config_file = c
        break

if config_file == str():
    raise FileNotFoundError("ERROR: config_file not found")
print(f"Warning-Bot starting at {datetime.now()} ...")
print(f"reading config from {config_file} ...")

# Parse Config File
config = configparser.RawConfigParser()
config.read(config_file)

def get_last_data_from_api():
    headers = {
        "Authorization": f"Bearer {config['API']['token']}"
    }
    r = post(f"http://{config['API']['host']}:{config['API']['port']}/get_latest/", headers=headers)
    if r.status_code == 200:
        return json.loads(r.json())
    else:
        return {}


def check_thresholds(data):
    print (data)
    for mp in data:
        for i in range(len(data[mp]['color'])):
            if data[mp]['color'][i] == 'warning':
                warn(
                    mp,
                    data[mp]['sensor_name'][i].split("\n")[0],
                    datetime.fromisoformat(data[mp]['dt'][i]),
                    data[mp]['value'][i],

                )
            elif data[mp]['color'][i] == 'alarm':
                alarm(
                    mp,
                    data[mp]['sensor_name'][i].split("\n")[0],
                    datetime.fromisoformat(data[mp]['dt'][i]),
                    data[mp]['value'][i],
                )
            elif data[mp]['color'][i] == 'alarm':
                dewarn()


def message_signal(message):
    print ("Warn via signal")
    print(message)


def message_email(message):
    print ("Warn via email")



def message_telegram(message):
    print ("Warn via telegram")


def select_channels_and_warn(message):
    if not config['warning']['enable']:
        print ("warning disabled...")

    else:
        if config['warning']['en_signal']:
            message_signal(message)

        if config['warning']['en_email']:
            message_email(message)

        if config['warning']['en_telegram']:
            message_telegram(message)


def warn(meas_point, sens_name, dt, value):
    text = config['warning']['message_warn']%(meas_point,sens_name, dt.strftime("%Y-%m-%d at %H:%M"), value)
    select_channels_and_warn(text)

def dewarn():
    text = config['warning']['message_dewarn']
    select_channels_and_warn(text)

def alarm(meas_point, sens_name, dt, value):
    text = config['warning']['message_alarm']%(meas_point,sens_name, dt.strftime("%Y-%m-%d at %H:%M"), value)
    select_channels_and_warn(text)

def dealarm():
    text = config['warning']['message_dealarm']
    select_channels_and_warn(text)


if __name__ == '__main__':
    data = get_last_data_from_api()
    check_thresholds(data)