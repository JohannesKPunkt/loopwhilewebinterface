#! /bin/bash
# Runs the docker container which is created by build_container.sh.
# The service will be available on port 80 of the host machine!
# The log files are placed locally in logs/.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Local directory, where the log files are placed
LOG_DIR=$SCRIPT_DIR/logs

sudo docker run --rm --name loopwhile -p 80:80 -v $LOG_DIR/supervisor:/var/log/supervisor -v $LOG_DIR/nginx:/var/log/nginx -v $LOG_DIR/loopwhile:/opt/loopwhile/logs loopwhile
