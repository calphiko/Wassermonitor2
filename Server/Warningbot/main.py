# WARNING BOT MAIN FILE

import os
from datetime import datetime, timedelta
import configparser
import json
from requests import post
import logging
import pytz

config_file = str()
config_file_pos = [os.path.abspath("../config.cfg"), os.path.abspath("../Server/config.cfg")]
for c in config_file_pos:
    print (os.path.abspath(c))
    if os.path.exists(c):
        config_file = c
        break

# Load messages from file
with open('../messages.json','r', encoding='utf-8') as f:
    messages = json.load(f)

# Parse Config File
config = configparser.RawConfigParser()
config.read(config_file)

# Loggerconfig
logger = logging.getLogger('wassermonitor warning bot')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

#now with timezone
now = datetime.now(tz=pytz.utc)
local_tz = pytz.timezone(config['warning']['timezone'])



if config_file == str():
    raise FileNotFoundError("ERROR: config_file not found")
logger.info(f"Warning-Bot starting at {now} ...")
logger.info(f"reading config from {config_file} ...")

# Parse Config File
config = configparser.RawConfigParser()
config.read(config_file)

def format_message(message_template, placeholders):
    return message_template.format(**placeholders)

def touch_file(filename):
    if os.path.exists(filename):
        os.utime(filename, None)
    else:
        with open(filename, 'a') as f:
            f.write(datetime.now(tz=pytz.utc).isoformat())
    logger.debug(f"lock file {filename} created...")


def destroy_file(filename):
    if os.path.exists(filename):
        with open (filename, 'r') as f :
            dt = datetime.fromisoformat(f.readline())
        os.remove(filename)
    logger.debug(f"lock file {filename} destroyed...")
    return dt


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
    warn_inverval = int(config["warning"]["deprecated_interval"])
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

            if datetime.fromisoformat(data[mp]['dt'][i]) < (now - timedelta(minutes=warn_inverval)):
                deprecated_warning(
                    mp,
                    data[mp]["sensor_name"][i].split("\n")[0],
                    datetime.fromisoformat(data[mp]['dt'][i])
                )
            else:
                dedeprecated_warning(
                    mp,
                    data[mp]["sensor_name"][i].split("\n")[0],

                )


def message_signal(message):
    logger.debug (f"Warn via signal\n\t{message}")


def message_email(message):
    logger.debug (f"Warn via email\n\t{message}")


def message_telegram(message):
    logger.debug (f"Warn via telegram\n\t{message}")


def select_channels_and_warn(message):
    if not config['warning']['enable']:
        logger.debug ("warning disabled...")

    else:
        if config['warning']['en_signal']:
            message_signal(message)

        if config['warning']['en_email']:
            message_email(message)

        if config['warning']['en_telegram']:
            message_telegram(message)


def warn(meas_point, sens_name, dt, value):
    filename = f"./{meas_point}-{sens_name}.warn"
    filename = os.path.abspath(filename)

    if not os.path.exists(filename):
        touch_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
            "date": dt.astimezone(local_tz).strftime(messages['dtformat'][config['API']['language']]),
            "value": value
        }
        text = format_message(messages['message_warn'][config['API']['language']], placeholders)
        logging.info("Users will be warned!")
        select_channels_and_warn(text)


def dewarn(meas_point, sens_name):
    filename = f"./{meas_point}-{sens_name}.warn"
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        dt = destroy_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
        }
        text = format_message(messages['message_dewarn'][config['API']['language']], placeholders)
        logging.info("Users will be dewarned!")
        select_channels_and_warn(text)


def alarm(meas_point, sens_name, dt, value):
    filename = f"./{meas_point}-{sens_name}.alarm"
    filename = os.path.abspath(filename)
    if not os.path.exists(filename):
        touch_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
            "date": dt.astimezone(local_tz).strftime(messages['dtformat'][config['API']['language']]),
            "value": value
        }
        text = format_message(messages['message_alarm'][config['API']['language']], placeholders)
        logging.info("Users will be alarmed!")
        select_channels_and_warn(text)


def dealarm(meas_point,sens_name ):
    filename = f"{meas_point}-{sens_name}.alarm"
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        dt = destroy_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
        }
        text = format_message(messages['message_dealarm'][config['API']['language']], placeholders)
        logging.info("Users will be dealarmed!")
        select_channels_and_warn(text)


def deprecated_warning(meas_point, sens_name, dt):
    filename = f"./{meas_point}-{sens_name}.dec"
    filename = os.path.abspath(filename)
    if not os.path.exists(filename):
        touch_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
            "date": dt.astimezone(local_tz).strftime(messages['dtformat'][config['API']['language']]),
        }
        text = format_message(messages['message_deprecated'][config['API']['language']], placeholders)
        logging.info("Users will get a deprecated warning!")
        select_channels_and_warn (text)


def dedeprecated_warning(meas_point, sens_name):
    filename = f"./{meas_point}-{sens_name}.dec"
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        dt = destroy_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
        }
        text = format_message(messages['message_dedeprecated'][config['API']['language']], placeholders)
        logging.info("Users will be dedeprecated!")
        select_channels_and_warn(text)

if __name__ == '__main__':
    data = get_last_data_from_api()
    check_thresholds(data)