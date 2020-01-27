#!/bin/bash
python3 src/Main.py --logfile=lwservice.log --host=127.0.0.1 --port=8080 --loglevel=DEBUG --max_sessions=1000 --ws_hostname=ws://127.0.0.1/lwservice/ --max_sessions_per_address=20 --report_file=report_data
