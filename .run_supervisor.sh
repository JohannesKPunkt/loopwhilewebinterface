#!/bin/bash
# Start script for use in docker container

set -e

# Import settings
source .settings.sh

# Set access rights for log directors
chown $LW_USER:$LW_GROUP "$LW_LOG_DIR/"

# Run supervisord
/usr/bin/supervisord
