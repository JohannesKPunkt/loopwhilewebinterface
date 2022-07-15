#!/bin/bash
# Fully-automatic install script
#
# This script will perform every step that is described in Chapter 2 of the doc

set -e

# Import settings
source .settings.sh

# Helper function for sed
function escape_path {
    # Replaces every '/' by '\/'
    echo "$1" | sed 's/\//\\\//g'
}


service_exists=
# Check if service already exists and stop it
if systemctl list-units --full -all | grep -Fq "$LW_SERVICENAME.service"; then
    echo "Stop lw service..."
    systemctl stop "$LW_SERVICENAME"
    service_exists=1
fi

# Install dependencies
echo "Install dependencies..."
apt-get update
apt-get install -y virtualenv
DEBIAN_FRONTEND="noninteractive" apt-get install -y nginx

# Create user if not existant
if ! id "$LW_USER" &>/dev/null; then
    echo "User $LW_USER does not exist and will be created..."
    useradd -M "$LW_USER" # -M means user without a home directory
    usermod -L "$LW_USER" # -L means password disabled - it is not possible to log in
fi

# Create directories
mkdir -p "$LW_INSTALL_DIR/logs"

# Install the application (seperate script)
./.deliver.sh LOCAL

# Setup virtualenv
"$LW_INSTALL_DIR/.setup_venv.sh"

# Setup nginx
cp config/nginx.example /etc/nginx/sites-available/default

# Setup lw service
cp config/lw.service "/etc/systemd/system/$LW_SERVICENAME.service"
sed -i "s/INSTALLATION_PATH/$(escape_path $LW_INSTALL_DIR)/g" "/etc/systemd/system/$LW_SERVICENAME.service"

# enable service, so that it will start automatically after reboot
echo "Enable lw service..."
systemctl enable "$LW_SERVICENAME"

# Start lw service
echo "Start lw service..."
systemctl start "$LW_SERVICENAME"

echo "Restart nginx..."
systemctl restart nginx

echo "### Setup successfull! ###"
