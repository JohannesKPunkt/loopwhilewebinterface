#!/bin/bash
# LW stop script
# If started as daemon, do not call this script directly,
# use 'sudo systemctl stop lw' instead!

pid="$(<pid)"
kill -s SIGINT "$pid"
