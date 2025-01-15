import unittest
from unittest.mock import patch, MagicMock
import os
import json
import sys
import logging
from datetime import datetime
import pytz
import configparser

sys.path.append(os.path.abspath("../../../Server/Warningbot/"))
from Server.Warningbot.warningbot import message_email

class TestMessageEmail(unittest.TestCase):


    @patch('builtins.open', create=True)
    @patch('json.load')
    @patch('smtplib.SMTP')
    @patch('logging.getLogger')

    def test_message_email_success(self, mock_get_logger, mock_smtp, mock_json_load, mock_open):
        """Tests successful email sending."""
        # Mock JSON configuration file
        mock_json_load.return_value = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "sender_email": "test@example.com",
            "sender_password": "password",
            "recipients": ["recipient1@example.com", "recipient2@example.com"]
        }

        # Mock SMTP server
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance

        # Mock file opening
        mock_open.return_value.__enter__.return_value = MagicMock()

        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Test data
        message = "Test message"
        subject = "Test Subject"

        # Call the function
        message_email(message, subject, logger=mock_logger)

        # Assertions for SMTP connection and sending
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("test@example.com", "password")
        mock_smtp_instance.sendmail.assert_called_once()

        # Assertions for logging
        mock_logger.info.assert_called()

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_message_email_file_not_found(self, mock_get_logger, mock_open):
        """Tests the case where the configuration file is missing."""

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with self.assertLogs(level='WARNING') as log:
            message_email("Test message", "Test Subject", logger=mock_logger)
            self.assertIn("Konfigurationsdatei", log.output[0])

    @patch('builtins.open', create=True)
    @patch('json.load', side_effect=json.JSONDecodeError("Expecting value", "", 0))
    def test_message_email_invalid_json(self, mock_get_logger, mock_json_load, mock_open):
        """Tests the case where the JSON configuration file is invalid."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with self.assertLogs(level='WARNING') as log:
            message_email("Test message", "Test Subject", logger=mock_logger)
            self.assertIn("Fehler beim Lesen der JSON-Datei", log.output[0])

    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_message_email_missing_configuration(self, mock_get_logger, mock_json_load, mock_open):
        """Tests the case where the JSON configuration is incomplete."""
        # Mock JSON configuration file with missing values
        mock_json_load.return_value = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587
            # Missing fields: sender_email, sender_password, recipients
        }

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with self.assertLogs(level='WARNING') as log:
            message_email("Test message", "Test Subject", logger=mock_logger)
            self.assertIn("missing email configuration", log.output[0])

    @patch('builtins.open', create=True)
    @patch('json.load')
    @patch('smtplib.SMTP', side_effect=Exception("SMTP error"))
    def test_message_email_smtp_error(self, mock_get_logger, mock_smtp, mock_json_load, mock_open):
        """Tests the case where an SMTP error occurs."""
        # Mock JSON configuration file
        mock_json_load.return_value = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "sender_email": "test@example.com",
            "sender_password": "password",
            "recipients": ["recipient1@example.com", "recipient2@example.com"]
        }

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with self.assertLogs(level='WARNING') as log:
            message_email("Test message", "Test Subject", logger=mock_logger)
            self.assertIn("Not able to send email", log.output[0])

        # Assertions for logging
        mock_logger.warning.assert_called()

if __name__ == '__main__':
    # LOAD CONFIGURATION FROM CONFIG FILE
    config_file = str()
    config_file_pos = [os.path.abspath("../config.cfg"), os.path.abspath("../Server/config.cfg"),
                       os.path.abspath("../../Server/config.cfg"), os.path.abspath("../../../Server/config.cfg")]
    for c in config_file_pos:
        print(os.path.abspath(c))
        if os.path.exists(c):
            config_file = c
            break

    # Parse Config File
    config = configparser.RawConfigParser()
    config.read(config_file)

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



    # now with timezone
    now = datetime.now(tz=pytz.utc)
    local_tz = pytz.timezone(config['warning']['timezone'])

    if config_file == str():
        raise FileNotFoundError("ERROR: config_file not found")
    logger.info(f"Warning-Bot starting at {now} ...")
    logger.info(f"reading config from {config_file} ...")
    unittest.main()
