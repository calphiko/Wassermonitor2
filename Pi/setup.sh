#!/bin/sh

# This is a setup script
# It will
#   1. Create python3 virtual environment
#   2. Install requirements.txt
#   3. Install gnuplot for plotting calib
#   4. Calibrate every single sensor that is configured
#   5. Generate key pair for data signing
#   6. Configure datacrawler as systemd-daemon
#   7. Configure datatransmitter as cron job every 5 minutes

# Please execute from the Pi directory! This is mandatory!!!!

echo "Installing wassermonitor pi daemons on your raspberry pi"

CONFIGFILENAME="config.json"
VENV_PATH="./.venv"

echo "\n\tChecking config file"
# TEST IF CONFIG FILE exists
if [ ! -f "$CONFIGFILENAME" ]; then
  echo "\t\tError: Config file $CONFIGFILENAME not found. Please create"
  exit 1
fi

# Überprüfen, ob die Datei Ausdrücke in spitzen Klammern enthält
if grep -q '<[^>]*>' "$CONFIGFILENAME"; then
    echo "\t\tError: Config file $CONFIGFILENAME contains default expressions in '<>'. Please replace with your configuration"
    exit 1
fi

echo "\n\tInstalling dependencies"
sudo apt update && sudo apt install -y  libopenblas-dev gnuplot

# CREATE PYTHON3 VENV

echo "\n\tCreating virtual environment and activate"
python3 -m venv $VENV_PATH
. "$VENV_PATH/bin/activate"


# Optional: Überprüfen, ob das venv erfolgreich aktiviert wurde
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Virtual environment could not be activated."
    exit 1
else
    echo "Virtual environment activated: $VIRTUAL_ENV"
fi

echo "\n\t Installing python requirements"
# INSTALL REQUIREMENTS.txt
pip3 install -r requirements.txt

# CALIBRATION
#python3 calib.py

# GENERATE KEY PAIR FOR DATA SIGNING
 #python3 generate_key_pair.py


