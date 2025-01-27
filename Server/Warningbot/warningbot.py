"""
Warning Bot Main File
======================

Overview
--------

This script implements the core functionality of a "Warning Bot" designed for monitoring and alerting based on sensor data thresholds. The bot reads configuration files and messages, retrieves data from an API, and triggers warnings, alarms, or notifications via multiple channels (e.g., Signal, email, Telegram).

Features
--------

- **Dynamic Configuration**: Loads configuration dynamically from predefined file paths.
- **API Integration**: Fetches the latest sensor data from a configured API endpoint.
- **Threshold Monitoring**: Checks sensor values against predefined thresholds to determine the severity of warnings or alarms.
- **Multichannel Alerts**:
  - Signal
  - Email
  - Telegram
- **Time-Zone Awareness**: Handles timestamps with full timezone support using `pytz`.
- **Logging**: Comprehensive logging for debugging and operational insights.
- **File-Based Lock Mechanism**: Creates and manages lock files to ensure consistent notification handling.

Dependencies
------------

- `os` for file handling.
- `datetime` and `pytz` for timezone-aware timestamps.
- `configparser` for configuration file parsing.
- `json` for working with message templates and API responses.
- `requests` for HTTP API communication.
- `logging` for structured logging.

Configuration Files
-------------------

1. **Configuration File** (`config.cfg`): Defines settings for API access, warning thresholds, and alerting channels.
2. **Messages File** (`messages.json`): Contains message templates for different alert types, supporting multiple languages.

Workflow
--------

1. **Initialization**:
   - Configuration and message files are loaded.
   - Logging is initialized.
2. **Data Retrieval**:
   - Fetch the latest sensor data from the API.
3. **Threshold Checking**:
   - Compare data against warning or alarm thresholds.
   - Handle deprecated or outdated sensor data.
4. **Notification Dispatch**:
   - Send alerts through enabled channels when necessary.
5. **File Management**:
   - Manage lock files for warnings and alarms to ensure notifications are sent appropriately.

Usage
-----

Run the script as the main file:

.. code-block:: bash

   python warning_bot.py

The bot will retrieve the latest sensor data, evaluate thresholds, and dispatch alerts based on the configuration.
"""

import os
from datetime import datetime, timedelta
import configparser
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from time import sleep

from requests import post
import logging
import pytz

# LOGGERCONFIG
logger = logging.getLogger('wassermonitor warning bot')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

now = datetime.now(tz=pytz.utc)


def load_config_from_file():
    # LOAD CONFIGURATION FROM CONFIG FILE
    config_file = str()
    config_file_pos = [os.path.abspath("../config.cfg"), os.path.abspath("../Server/config.cfg"),
                       os.path.abspath("../../Server/config.cfg"), os.path.abspath("../../../Server/config.cfg")]
    for c in config_file_pos:
        print(os.path.abspath(c))
        if os.path.exists(c):
            config_file = c
            break

    if config_file == str():
        raise FileNotFoundError("ERROR: config_file not found")

    logger.info(f"reading config from {config_file} ...")

    # Parse Config File
    config = configparser.RawConfigParser()
    config.read(config_file)

    return config



def load_msgs_from_json():
    # LOAD MESSAGES FROM JSON
    msg_json = str()
    msg_json_pos = [os.path.abspath('../messages.json'), os.path.abspath("../Server/messages.json"),
                    os.path.abspath("../../Server/messages.json"), os.path.abspath("../../../Server/messages.json")]
    for c in msg_json_pos:
        print(os.path.abspath(c))
        if os.path.exists(c):
            msg_json = c
            break
    with open(msg_json, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    return messages

def format_message(message_template, placeholders):
    """
    Formats a message template by replacing placeholders with provided values.

    This function uses Python's string formatting to substitute placeholders
    in the given message template with corresponding values from a dictionary.

    :param message_template: The template string containing placeholders in the form `{placeholder_name}`.
    :type message_template: str
    :param placeholders: A dictionary containing placeholder names as keys and their replacement values.
    :type placeholders: dict
    :return: The formatted message with placeholders replaced by their corresponding values.
    :rtype: str

    :raises KeyError: If a placeholder in the template is not found in the `placeholders` dictionary.

    """
    return message_template.format(**placeholders)

def touch_file(filename):
    """
    Creates or updates a lock file with the current UTC timestamp.

    If the specified file exists, its modification time is updated.
    If it does not exist, the file is created and the current UTC timestamp is written to it.

    :param filename: The path to the lock file.
    :type filename: str
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        touch_file("example.lock")
    """

    if os.path.exists(filename):
        os.utime(filename, None)
    else:
        with open(filename, 'a') as f:
            f.write(datetime.now(tz=pytz.utc).isoformat())
    logger.debug(f"lock file {filename} created...")


def destroy_file(filename):
    """
     Deletes a lock file and returns its timestamp.

     If the specified file exists, its contents (assumed to be an ISO-formatted
     timestamp) are read and returned, and the file is then deleted.

     :param filename: The path to the lock file.
     :type filename: str
     :return: The timestamp read from the lock file.
     :rtype: datetime.datetime

     **Example**:

     .. code-block:: python

         dt = destroy_file("example.lock")
         print(f"Lock file destroyed, timestamp was: {dt}")
     """

    if os.path.exists(filename):
        with open (filename, 'r') as f :
            dt = datetime.fromisoformat(f.readline())
        os.remove(filename)
    logger.debug(f"lock file {filename} destroyed...")
    return dt


def get_last_data_from_api():
    """
    Retrieves the latest data from the API.

    Sends a POST request to the configured API endpoint with an authorization token.
    If the request is successful (HTTP status 200), the response is parsed and returned
    as a Python dictionary. Otherwise, an empty dictionary is returned.

    :return: The latest data retrieved from the API, or an empty dictionary if the request fails.
    :rtype: dict

    **Example**:

    .. code-block:: python

        data = get_last_data_from_api()
        if data:
            print("Data retrieved successfully:", data)
        else:
            print("Failed to retrieve data.")
    """

    headers = {
        "Authorization": f"Bearer {config['API']['token']}"
    }
    r = post(f"http://{config['API']['host']}:{config['API']['port']}/get_latest/", headers=headers)
    if r.status_code == 200:
        return json.loads(r.json())
    else:
        return {}


def check_thresholds(data, config, messages):
    """
    Evaluates sensor data against thresholds and triggers corresponding actions.

    This function iterates over the provided sensor data and performs the following:
    - Triggers warnings or alarms based on the sensor's color status (`warning` or `alarm`).
    - Revokes warnings if conditions are resolved.
    - Handles deprecated warnings if the sensor data is older than the configured interval.

    :param data: The sensor data, structured as a dictionary with measurement points as keys.
                 Each measurement point contains color statuses, sensor names, timestamps, and values.
    :type data: dict
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        sensor_data = {
            "point1": {
                "color": ["warning", "ok"],
                "sensor_name": ["Temperature", "Pressure"],
                "dt": ["2025-01-10T10:00:00Z", "2025-01-10T10:05:00Z"],
                "value": [75, 1.2]
            }
        }
        check_thresholds(sensor_data)
    """
    print (config)
    print (messages)
    warn_inverval = int(config["warning"]["deprecated_interval"])

    for mp in data:
        for i in range(len(data[mp]['color'])):
            if data[mp]['color'][i] == 'warning':
                warn(
                    mp,
                    data[mp]['sensor_name'][i].split("\n")[0],
                    datetime.fromisoformat(data[mp]['dt'][i]),
                    data[mp]['value'][i],
                    config,
                    messages

                )
            elif data[mp]['color'][i] == 'alarm':
                alarm(
                    mp,
                    data[mp]['sensor_name'][i].split("\n")[0],
                    datetime.fromisoformat(data[mp]['dt'][i]),
                    data[mp]['value'][i],
                    config,
                    messages
                )
            elif data[mp]['color'][i] == 'alarm':
                dewarn(
                    config,
                    messages
                )

            if datetime.fromisoformat(data[mp]['dt'][i]) < (now - timedelta(minutes=warn_inverval)):
                deprecated_warning(
                    mp,
                    data[mp]["sensor_name"][i].split("\n")[0],
                    datetime.fromisoformat(data[mp]['dt'][i]),
                    config,
                    messages
                )
            else:
                dedeprecated_warning(
                    mp,
                    data[mp]["sensor_name"][i].split("\n")[0],
                    config,
                    messages
                )


def message_signal(message, config, messages):
    """
    To be implemented

    :param message:
    :return:
    """

    logger.debug (f"Warn via signal\n\t{message}")

def load_email_creds_from_file():
    """
    Loads email credentials from a local JSON file.

    This function reads the `creds.json` file from the `./email/` directory
    and returns the parsed content as a dictionary. The credentials file should
    include the required fields for email operations, such as SMTP server details,
    email addresses, and passwords.

    :return: A dictionary containing email credentials, or None if the file is not found or cannot be parsed.
    :rtype: dict | None

    :raises json.JSONDecodeError: If the `creds.json` file contains invalid JSON.
    :raises FileNotFoundError: If the `creds.json` file is missing.

    **Example**:

    .. code-block:: python

        email_creds = load_email_creds_from_file()
        if email_creds:
            print("Email credentials loaded successfully.")
        else:
            print("Failed to load email credentials.")

    **Notes**:
    - The `creds.json` file should be located in the `./email/` directory.
    - If the file is missing, ensure it is created and populated with the correct fields.
    - The structure of the `creds.json` file is as follows:

    .. code-block:: json

        {
            "smtp_server": "smtp.example.com",
            "port": 587,
            "username": "your_email@example.com",
            "password": "your_password"
        }
    """

    creds_path = os.path.abspath('./email/creds.json')

    try:
        with open(creds_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.warning(f"Config file '{creds_path}' not found.")
        return
    except json.JSONDecodeError:
        logger.warning(f"Cannot parse JSON file {creds_path}. Please check format...")
        return

def message_email(message, subject, config, messages):
    """
    Sends an email with the specified message and subject.

    This function loads email server credentials and configurations from a local JSON file
    and sends an email to the specified recipients. The function logs the operation and
    handles common errors, such as missing configuration or failed email sending.

    :param message: The message body to be sent via email.
    :type message: str
    :param subject: The subject line of the email.
    :type subject: str
    :return: None

    :raises FileNotFoundError: If the `creds.json` configuration file is missing.
    :raises json.JSONDecodeError: If the `creds.json` file contains invalid JSON.
    :raises KeyError: If required fields (e.g., `smtp_server`, `recipients`) are missing in the configuration.
    :raises smtplib.SMTPException: If an error occurs during the SMTP connection or email sending.

    **Example**:

    .. code-block:: python

        message_email("System alert: CPU usage exceeds 90%.", "High CPU Usage Alert")

    **Notes**:
    - The `creds.json` file should be located in the `./email/` directory.
    - It must include the following fields:
        - `smtp_server`: The SMTP server address.
        - `smtp_port`: The SMTP server port.
        - `sender_email`: The sender's email address.
        - `sender_password`: The sender's email password.
        - `recipients`: A list of recipient email addresses.

    **Structure of `creds.json`**:

    .. code-block:: json

        {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "sender_email": "your_email@example.com",
            "sender_password": "your_password",
            "recipients": [
                "recipient1@example.com",
                "recipient2@example.com"
            ]
        }
    """

    logger.debug (f"Warn via email\n\t{message}")
    #print(f"Warn via email\n\t{message}")

    mail_config = load_email_creds_from_file()

    # Extrahiere die Konfigurationswerte
    smtp_server = mail_config.get("smtp_server")
    smtp_port = mail_config.get("smtp_port")
    sender_email = mail_config.get("sender_email")
    sender_password = mail_config.get("sender_password")
    recipients = mail_config.get("recipients")
    subject = subject
    body = message

    if not all([smtp_server, smtp_port, sender_email, sender_password, recipients, subject, body]):
        logging.warning("missing email configuration in JSON File")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with (smtplib.SMTP(smtp_server, smtp_port)) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())


        logger.info("Mail successfully sent.")
    except Exception as e:
        logger.warning(f"Not able to send email: {e}")



def load_telegram_creds_from_file():
    """
    Loads Telegram bot credentials from a local JSON file.

    This function reads the `creds.json` file from the `./telegram/` directory
    and returns the parsed content as a dictionary. The credentials file should
    include fields required for Telegram bot operations, such as `api_token` and `group_id`.

    :return: A dictionary containing the Telegram bot credentials, or False if the file does not exist.
    :rtype: dict | bool

    :raises json.JSONDecodeError: If the `creds.json` file contains invalid JSON.
    :raises FileNotFoundError: If the `creds.json` file is missing.
    :raises KeyError: If required fields (e.g., `api_token` or `group_id`) are missing in the credentials file.

    **Example**:

    .. code-block:: python

        credentials = load_telegram_creds_from_file()
        if credentials:
            print("Credentials loaded successfully.")
        else:
            print("Credentials file not found.")

    **Notes**:
    - The `creds.json` file should be located in the `./telegram/` directory.
    - If the file is missing, create it from the provided template `creds.json.tmpl`.
    - The structure of the `creds.json` file is as follows:

    .. code-block:: json

        {
            "api_token": "your_bot_token",
            "group_id": "your_chat_id"
        }
    """
    creds_path = os.path.abspath('./telegram/creds.json')

    # Load tgram credentials from file
    if not os.path.exists(creds_path):
        print(
            "No creds.json found. Please copy the creds.json.tmpl file to creds.json and add your telegram bot credentials.")
        return False

    with open(creds_path, 'r', encoding='utf-8') as f:
        return json.load(f)



def message_telegram(message, config, messages):
    """
    Sends a message via Telegram to a configured group or chat.

    This function loads Telegram bot credentials from a local JSON file and
    sends the provided message to the specified chat or group. The function
    logs the operation and returns whether the message was successfully sent.

    :param message: The message text to be sent via Telegram.
    :type message: str
    :return: True if the message was successfully sent, False otherwise.
    :rtype: bool

    :raises FileNotFoundError: If the `creds.json` file is missing.
    :raises KeyError: If required fields (e.g., `api_token` or `group_id`) are missing in the credentials file.

    **Example**:

    .. code-block:: python

        if message_telegram("Alert: Sensor threshold exceeded!"):
            print("Message sent successfully.")
        else:
            print("Failed to send message.")

    **Notes**:
    - The `creds.json` file should be located in the `./telegram/` directory.
    - It must include `api_token` and `group_id` fields.

    **Structure of `creds.json`**:

    .. code-block:: json

        {
            "api_token": "your_bot_token",
            "group_id": "your_chat_id"
        }
    """

    logger.debug (f"Warn via telegram\n\t{message}")
    tgram_creds = load_telegram_creds_from_file()

    bot_token = tgram_creds['api_token']
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    data = {
        "chat_id": tgram_creds["group_id"],
        "text": message
    }

    response = post(url, data=data)

    if response.json()['ok'] == True:
        return True
    else:
        return False

def select_channels_and_warn(message, config, messages):
    """
    Sends a warning message through enabled communication channels.

    Based on the configuration, this function sends the provided message via
    Signal, email, or Telegram. If warnings are disabled in the configuration,
    no action is taken.

    :param message: The warning message to be sent.
    :type message: str
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        select_channels_and_warn("Threshold exceeded for sensor A.")

    **Notes**:
    - The function checks the following configuration keys under the `warning` section:
        - `enable`: If `False`, no messages are sent.
        - `en_signal`: Enables sending messages via Signal.
        - `en_email`: Enables sending messages via email.
        - `en_telegram`: Enables sending messages via Telegram.
    """

    if not config.getboolean('warning','enable'):
        logger.debug ("warning disabled...")

    else:
        if config.getboolean('warning','en_signal'):
            message_signal(message, config, messages)

        if config.getboolean('warning','en_email'):
            message_email(message, messages['email_subject'][config['API']['language']], config, messages)

        if config.getboolean('warning','en_telegram'):
            message_telegram(message, config, messages)


def warn(meas_point, sens_name, dt, value, config, messages):
    """
    Issues a warning for a specific measurement point and sensor.

    This function creates a warning file to indicate an active warning for
    the given measurement point and sensor. If the warning file does not
    already exist, it formats a warning message using placeholders and sends
    the message through the configured communication channels.

    :param meas_point: The identifier of the measurement point.
    :type meas_point: str
    :param sens_name: The name of the sensor triggering the warning.
    :type sens_name: str
    :param dt: The timestamp of the warning event.
    :type dt: datetime.datetime
    :param value: The sensor value triggering the warning.
    :type value: float or int
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        warn(
            meas_point="point1",
            sens_name="Sens1",
            dt=datetime.now(tz=pytz.utc),
            value=75.3
        )

    **Notes**:
    - The function creates a warning file named `{meas_point}-{sens_name}.warn`.
    - The message format and language are determined by the `messages` and
      `config['API']['language']` settings.
    - The message includes the sensor name, measurement point, date (localized),
      and value.
    """

    filename = f"./{meas_point}-{sens_name}.warn"
    filename = os.path.abspath(filename)
    local_tz = pytz.timezone(config['warning']['timezone'])
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
        select_channels_and_warn(text, config, messages)


def dewarn(meas_point, sens_name, config, messages):
    """
    Removes a warning and notifies users that the warning has been lifted.

    This function checks for the existence of a warning file for the specified
    measurement point and sensor. If the warning file exists, it is destroyed,
    and a message is sent to notify users that the warning has been cleared.
    The message is sent via the configured communication channels.

    :param meas_point: The identifier of the measurement point.
    :type meas_point: str
    :param sens_name: The name of the sensor whose warning is being cleared.
    :type sens_name: str
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        dewarn(meas_point="point1", sens_name="Sens1")

    **Notes**:
    - The function looks for a warning file named `{meas_point}-{sens_name}.warn`.
    - If the file exists, it is destroyed, and users are notified via the selected channels.
    - The message includes the sensor and measurement point but does not include a value.
    """

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
        select_channels_and_warn(text, config, messages)


def alarm(meas_point, sens_name, dt, value, config, messages):
    """
    Issues an alarm for a specific measurement point and sensor.

    This function creates a warning file to indicate an active alarm for
    the given measurement point and sensor. If the alarm file does not
    already exist, it formats an alarm message using placeholders and sends
    the message through the configured communication channels.

    :param meas_point: The identifier of the measurement point.
    :type meas_point: str
    :param sens_name: The name of the sensor triggering the warning.
    :type sens_name: str
    :param dt: The timestamp of the warning event.
    :type dt: datetime.datetime
    :param value: The sensor value triggering the warning.
    :type value: float or int
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        alarm(
            meas_point="point1",
            sens_name="Sens1",
            dt=datetime.now(tz=pytz.utc),
            value=75.3
        )

    **Notes**:
    - The function creates a warning file named `{meas_point}-{sens_name}.alarm`.
    - The message format and language are determined by the `messages` and
      `config['API']['language']` settings.
    - The message includes the sensor name, measurement point, date (localized),
      and value.
    """

    filename = f"./{meas_point}-{sens_name}.alarm"
    filename = os.path.abspath(filename)
    local_tz = pytz.timezone(config['warning']['timezone'])
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
        select_channels_and_warn(text, config, messages)


def dealarm(meas_point,sens_name, config, messages ):
    """
    Removes a alarm and notifies users that the warning has been lifted.

    This function checks for the existence of an alarm file for the specified
    measurement point and sensor. If the alarm file exists, it is destroyed,
    and a message is sent to notify users that the alarm has been cleared.
    The message is sent via the configured communication channels.

    :param meas_point: The identifier of the measurement point.
    :type meas_point: str
    :param sens_name: The name of the sensor whose warning is being cleared.
    :type sens_name: str
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        dealarm(meas_point="point1", sens_name="Sens1")

    **Notes**:
    - The function looks for a warning file named `{meas_point}-{sens_name}.alarm`.
    - If the file exists, it is destroyed, and users are notified via the selected channels.
    - The message includes the sensor and measurement point but does not include a value.
    """

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
        select_channels_and_warn(text, config, messages)


def deprecated_warning(meas_point, sens_name, dt, config, messages):
    """
   Issues a deprecated warning for a specific measurement point and sensor.

   This function creates a deprecated warning file for the given measurement
   point and sensor. If the deprecated warning file does not already exist,
   it formats a warning message and sends it through the configured
   communication channels.

   :param meas_point: The identifier of the measurement point.
   :type meas_point: str
   :param sens_name: The name of the sensor triggering the deprecated warning.
   :type sens_name: str
   :param dt: The timestamp of when the deprecated warning occurred.
   :type dt: datetime.datetime
   :return: None
   :rtype: None

   **Example**:

   .. code-block:: python

       deprecated_warning(
           meas_point="point1",
           sens_name="Sens1",
           dt=datetime.now(tz=pytz.utc)
       )

   **Notes**:
   - The function creates a deprecated warning file named `{meas_point}-{sens_name}.dec`.
   - The message format and language are determined by the `messages` and
     `config['API']['language']` settings.
   - The message includes the sensor name, measurement point, and the date
     (localized) when the warning was issued.
   """

    filename = f"./{meas_point}-{sens_name}.dec"
    filename = os.path.abspath(filename)
    local_tz = pytz.timezone(config['warning']['timezone'])
    if not os.path.exists(filename):
        touch_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
            "date": dt.astimezone(local_tz).strftime(messages['dtformat'][config['API']['language']]),
        }
        text = format_message(messages['message_deprecated'][config['API']['language']], placeholders)
        logging.info("Users will get a deprecated warning!")
        select_channels_and_warn (text, config, messages)


def dedeprecated_warning(meas_point, sens_name, config, messages):
    """
    Removes a deprecated warning and notifies users that the warning has been lifted.

    This function checks for the existence of a deprecated warning file for the
    specified measurement point and sensor. If the deprecated warning file exists,
    it is destroyed, and a message is sent to notify users that the deprecated warning
    has been cleared. The message is sent through the configured communication channels.

    :param meas_point: The identifier of the measurement point.
    :type meas_point: str
    :param sens_name: The name of the sensor whose deprecated warning is being cleared.
    :type sens_name: str
    :return: None
    :rtype: None

    **Example**:

    .. code-block:: python

        dedeprecated_warning(meas_point="point1", sens_name="Sens1")

    **Notes**:
    - The function looks for a deprecated warning file named `{meas_point}-{sens_name}.dec`.
    - If the file exists, it is destroyed, and users are notified via the selected channels.
    - The message includes the sensor and measurement point but does not include a date.
    """

    filename = f"./{meas_point}-{sens_name}.dec"
    filename = os.path.abspath(filename)
    local_tz = pytz.timezone(config['warning']['timezone'])
    if os.path.exists(filename):
        dt = destroy_file(filename)
        placeholders = {
            "sensor": sens_name,
            "meas_point": meas_point,
            "date": dt.astimezone(local_tz).strftime(messages['dtformat'][config['API']['language']]),
        }
        text = format_message(messages['message_dedeprecated'][config['API']['language']], placeholders)
        logging.info("Users will be dedeprecated!")
        select_channels_and_warn(text, config, messages)






if __name__ == '__main__':

    config = load_config_from_file()
    messages = load_msgs_from_json()
    # now with timezone
    logger.info(f"Warning-Bot starting at {now} ...")

    while True:
        #print (config))
        data = get_last_data_from_api()
        logger.info(f"Got data from API at {now}")
        check_thresholds(data, config, messages)
        sleep(60)