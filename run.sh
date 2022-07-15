#!/bin/bash

# Import settings
source .settings.sh

# Use virtualenv (if it is set up)
if [ -d "$LW_VENV_NAME" ]
then
    source "$LW_VENV_NAME/bin/activate"
fi

python3 src/Main.py --logfile="$LW_LOG_DIR/lwservice.log" --host=127.0.0.1 --port=8080 "--loglevel=$LW_LOG_LEVEL" "--max_sessions=$LW_MAX_SESSIONS" "--max_sessions_per_address=$LW_MAX_SESSIONS_PER_ADDRESS" "--user_src=$LW_USER_SRC_DIR" --report_file="$LW_LOG_DIR/report_data"

# Leave virtualenv (if it is set up)
if [ -d "$LW_VENV_NAME" ]
then
    deactivate
fi
