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

SERVICE_USER="wm2"

# CREATE NEW USER FOR DAEMON
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    echo "Create new user: $SERVICE_USER"
    sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
else
    echo "User $SERVICE_USER already exists."
fi

sudo chown -R $SERVICE_USER:$SERVICE_USER ./

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
sudo -u $SERVICE_USER python3 -m venv $VENV_PATH


# Optional: Überprüfen, ob das venv erfolgreich aktiviert wurde
#if [ -z "$VIRTUAL_ENV" ]; then
#    echo "Error: Virtual environment could not be activated."
#    exit 1
#else
#    echo "Virtual environment activated: $VIRTUAL_ENV"
#fi

echo "\n\t Installing python requirements"
# INSTALL REQUIREMENTS.txt
sudo -u $SERVICE_USER $VENV_PATH/bin/pip3 install -r requirements.txt

# CALIBRATION
echo "\n\t Configuring sensors"
sudo -u $SERVICE_USER $VENV_PATH/bin/python3 configure_sensors.py

# GENERATE KEY PAIR FOR DATA SIGNING
sudo -u $SERVICE_USER $VENV_PATH/bin/python3 generate_key_pair.py

# INSTALL datacrawler AS SYSTEM DAEMON
echo ""
echo "CREATE SYSTEMD DAEMON FOR DATASCRAWLER"

SERVICE_NAME="wassermonitor_datascrawler"
PYTHON_PROGRAMM="datacrawler.py"
CURRENT_DIR=$(pwd)
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"



# CREATE SERVICE FILE
echo "Create systemd-service file: $SERVICE_FILE"
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=$SERVICE_NAME
After=network.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/.venv/bin/python3 $CURRENT_DIR/$PYTHON_PROGRAM
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL


echo "Load and enable daemon"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# INSTALL datatransmitter AS CRON JOB
echo ""
echo "CREATE CRONJOB FOR SUBMITTING THE DATA"

CRON_SCRIPT="datatransmitter.py"
CRON_FILE="/var/spool/cron/crontabs/$SERVICE_USER"

echo "CRON JOB THAT RUNS EVERY 5 MINUTES..."
CRON_ENTRY="*/5 * * * * $CURRENT_DIR/.venv/bin/python3 $CURRENT_DIR/$CRON_SCRIPT"

# Sicherstellen, dass die Crontab-Datei für den Benutzer existiert
if [ ! -f "$CRON_FILE" ]; then
    echo "Create new crontab for user $SERVICE_USER"
    sudo touch "$CRON_FILE"
    sudo chmod 600 "$CRON_FILE"
    sudo chown "$SERVICE_USER":"$SERVICE_USER" "$CRON_FILE"
fi

# Cronjob hinzufügen, falls er noch nicht existiert
if sudo crontab -u "$SERVICE_USER" -l 2>/dev/null | grep -qF "$CRON_ENTRY"; then
    echo "Cronjob already exists."
else
    (sudo crontab -u "$SERVICE_USER" -l 2>/dev/null; echo "$CRON_ENTRY") | sudo crontab -u "$SERVICE_USER" -
    echo "Cronjob successfully added."
fi

# Status überprüfen
echo "Current Cronjobs $SERVICE_USER:"
sudo crontab -u "$SERVICE_USER" -l

echo ""
echo "For uploading data to the API, please add this public key to your APIs authorized-keys file (Consider Server documentation)."
cat $CURRENT_DIR/.psk/public_key.rsa
echo ""