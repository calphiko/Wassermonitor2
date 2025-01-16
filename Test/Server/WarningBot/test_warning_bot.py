import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import json
import sys
import logging
from datetime import datetime, timedelta
import pytz
import configparser

from black.handle_ipynb_magics import MagicFinder

sys.path.append(os.path.abspath("../../../Server/Warningbot/"))

def dict_to_configparser(data):
    config = configparser.ConfigParser()
    for section, values in data.items():
        config[section] = values
    return config

#from Server.Warningbot.warningbot import check_thresholds

class TestWarningBot(unittest.TestCase):
    @patch('Server.Warningbot.warningbot.smtplib.SMTP')
    @patch('Server.Warningbot.warningbot.post')
    @patch('Server.Warningbot.warningbot.os.path.exists')
    @patch('Server.Warningbot.warningbot.touch_file')
    @patch('Server.Warningbot.warningbot.load_email_creds_from_file')
    @patch('Server.Warningbot.warningbot.load_telegram_creds_from_file')
    def test_full_chain(self,  mock_tgram_creds, mock_email_creds, mock_touch_file, mock_exists, mock_post, mock_smtp):
        mock_exists.return_value = False
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        mock_post.return_value.json.return_value = {
            "ok" : True
        }

        now = datetime.now(tz=pytz.utc)

        data = {
            "raspi1": {
                "color": ["normal","warning", "alarm"],
                "sensor_name": ["Sens1", "Sens2", "Sens3"],
                "dt": [
                    (now - timedelta(minutes=0)).isoformat(),
                    (now - timedelta(minutes=30)).isoformat(),
                    (now - timedelta(minutes=10)).isoformat(),
                ],
                "value": [75, 72, 63],
            }
        }

        # Inhalte der `messages.json`
        mocked_messages_content = json.dumps({
            "message_warn": {"en": "Warning: {sensor} at {meas_point}, value {value}"},
            "message_alarm": {"en": "Alarm: {sensor} at {meas_point}, value {value}"},
            "message_deprecated": {"en": "Decrepation: {sensor} at {meas_point}, value is from {date}. too old."},
            "dtformat": {"en": "%Y-%m-%d %H:%M:%S"},
            "email_subject": {"en": "Threshold Alert"}
        })

        # Inhalte der `config.cfg`
        mocked_config_content = {
            "warning": {
                "enable": "on",
                "en_signal": "on",
                "en_email": "on",
                "en_telegram": "on",
                "deprecated_interval": "16",
                "timezone": "Europe/Berlin",
            },
            "API": {
                "language": "en",
                "token": "test-token",
                "host": "localhost",
                "port": "5000",
            },
        }

        mock_email_creds.return_value = {
            "smtp_server": "smtp.example.com",
            "smtp_port": "587",
            "sender_email": "your_email@example.com",
            "sender_password": "password",
            "recipients": [
                "cp@koppen.me",
                "carl.philipp@koppen-siegen.de",
                "carl.ph.koppen@gmail.com"
            ]
        }

        mock_tgram_creds.return_value = {
            "name": "TestBot",
            "api_token": "TestToken",
            "group_name": "WmTest",
            "group_id": "YOUR_GROUP_ID"
        }

        mocked_config_content = dict_to_configparser(mocked_config_content)

        # Überprüfe, ob die Funktion korrekt gemockt wurde
        self.assertIsNotNone(mock_email_creds.return_value)
        self.assertEqual(mock_email_creds.return_value['smtp_server'], "smtp.example.com")

        #mock_msgs.return_value = json.loads(mocked_messages_content)
        #mock_config.return_value = mocked_config_content

        # Mock für `configparser.RawConfigParser`
        #mock_config_instance = MagicMock()
        #mock_config_instance.__getitem__.side_effect = mocked_config_content.__getitem__
        #mock_config_instance.get.side_effect = lambda section, key: mocked_config_content[section][key]
        #mock_configparser.return_value = mock_config_instance

        # Funktion `check_thresholds` importieren und aufrufen
        with patch('warningbot.now', mocked_config_content):
            from Server.Warningbot.warningbot import check_thresholds
            check_thresholds(data, mocked_config_content, json.loads(mocked_messages_content))

        # Assertions für Email
        #mock_smtp.assert_called_once_with("smtp.example.com", 587)  # Beispiel-Konfig
        # Überprüfe, ob der Mock dreimal aufgerufen wurde
        self.assertEqual(mock_smtp.call_count, 3)
        self.assertEqual(mock_smtp_instance.starttls.call_count, 3)
        mock_smtp_instance.login.assert_called_with("your_email@example.com", "password")
        mock_smtp_instance.sendmail.assert_called()

        # Assertions für Telegram
        mock_post.assert_called_with(
            "https://api.telegram.org/botTestToken/sendMessage",
            data={
                "chat_id": "YOUR_GROUP_ID",
                "text": ANY
            }
        )

        # Assertions für Dateien
        mock_touch_file.assert_any_call(os.path.abspath("./raspi1-Sens2.dec"))
        mock_touch_file.assert_any_call(os.path.abspath("./raspi1-Sens2.warn"))
        mock_touch_file.assert_any_call(os.path.abspath("./raspi1-Sens3.alarm"))

if __name__ == '__main__':
    unittest.main()