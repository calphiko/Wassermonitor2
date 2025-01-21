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

# CREATE PYTHON3 VENV
python3 -m venv ../.venv
source ../.venv/bin/activate

# INSTALL REQUIREMENTS.txt
python3 install -r ../requirements.txt

# INSTALL GNUPLOT
sudo apt update && sudo apt install gnuplot

# CALIBRATION

# GENERATE KEY PAIR FOR DATA SIGNING
# python3 generate_key_pair.py

