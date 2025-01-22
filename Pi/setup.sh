#!/bin/bash

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

CONFIGFILENAME="config.json"

# TEST IF CONFIG FILE exists
if [[ ! -f "$CONFIGFILENAME"]]; then
  echo "Error: Config file $CONFIGFILENAME not found. Please create"
  exit 1
fi

# Überprüfen, ob die Datei Ausdrücke in spitzen Klammern enthält
if grep -q '<[^>]*>' "$DATEI"; then
    echo "Error: Config file $CONFIGFILENAME contains default expressions in '<>'. Please replace with your configuration"
    exit 1
fi

sudo apt update && sudo apt install -y  libopenblas-dev gnuplot

# CREATE PYTHON3 VENV
python3 -m venv .venv
source .venv/bin/activate

# INSTALL REQUIREMENTS.txt
pip3 install -r requirements.txt

# EDIT config.json

# CALIBRATION
python3 calib.py

# GENERATE KEY PAIR FOR DATA SIGNING
 python3 generate_key_pair.py


