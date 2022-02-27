# This file contains the configuration of the
# loopwhile interactive interpreter service.
# Changing these settings might require a reinstall!


# Log level
export LW_LOG_LEVEL="DEBUG"

# Maximum number of parallel user sessions
export LW_MAX_SESSIONS="1000"

# Maximum number of parallel sessions per user
export LW_MAX_SESSIONS_PER_ADDRESS="20"

## The settings below should usually not be changed

# User and group of the service deamon
export LW_USER="loopwhile"
export LW_GROUP="$LW_USER"

# Installation directory
export LW_INSTALL_DIR="/opt/loopwhile"

# Log directory
export LW_LOG_DIR="$LW_INSTALL_DIR/log"

# Directory where temporary files of the execution are stored
export LW_USER_SRC_DIR="/tmp/loopwhile_user_src"

# Directory where files that should be served by nginx are stored
export LW_HTTPD_DIR="/var/www/html"
