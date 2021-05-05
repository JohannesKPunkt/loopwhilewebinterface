#!/bin/bash

# Import settings
source settings.sh

python3 src/Main.py --logfile="$LW_LOG_DIR/lwservice.log" --host=127.0.0.1 --port=8080 "--loglevel=$LW_LOG_LEVEL" "--max_sessions=$LW_MAX_SESSIONS" "--ws_hostname=ws://$LW_WEBSOCKETS_URL/lwservice/" "--max_sessions_per_address=$LW_MAX_SESSIONS_PER_ADDRESS" "--user_src=$LW_USER_SRC_DIR" --report_file="$LW_LOG_DIR/report_data"
