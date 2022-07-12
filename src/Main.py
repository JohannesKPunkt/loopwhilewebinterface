#  Main.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#
#

import waitress
from tg import MinimalApplicationConfigurator
from tg.configurator.components.statics import StaticsConfigurationComponent

import sys
import os

import Logging
from ArgParser import ArgParser

_host = None
_port = None
logger = None

if __name__ == '__main__':
    # Process arguments
    try:
        arg_parser = ArgParser(sys.argv[1:], ["--host=", "--port=", "--loglevel=",
            "--logfile=", "--user_src=", "--max_sessions=", "--ws_hostname=", "--report_file=",
            "--ws_interface=", "--ws_port=", "--max_sessions_per_address="], True)
        _host = arg_parser.get_value_default("--host", "127.0.0.1")
        _port = int(arg_parser.get_value_default("--port", "8080"))
        _loglevel = arg_parser.get_value_default("--loglevel", "INFO")
        _logfile = arg_parser.get_value_default("--logfile", None)
        _user_src = arg_parser.get_value_default("--user_src", "./user_src")
        _max_sessions = int(arg_parser.get_value_default("--max_sessions", "200"))
        _max_sessions_per_addr = int(arg_parser.get_value_default("--max_sessions_per_address", "10"))
        _ws_host = arg_parser.get_value_default("--ws_hostname", None)
        _ws_interface = arg_parser.get_value_default("--ws_interface", "127.0.0.1")
        _ws_port = int(arg_parser.get_value_default("--ws_port", "8081"))
        _report_file = arg_parser.get_value("--report_file")
    except Exception as e:
        print("Exception while parsing arguments: " + str(e))
        sys.exit(-1)

    # Prepare logging
    Logging.set_global_options(_loglevel, _logfile)
    logger = Logging.get_logger(__name__)


from Controller import Controller
from WebSockets import WebSocketsService
import ReportGenerator

if __name__ == '__main__':
    if _ws_host is not None:
        logger.info("Note: option --ws_hostname is deprecated")
    # Write PID file for stop.sh script
    pid = os.getpid()
    with open("pid", "w") as pidfile:
        pidfile.write(str(pid))

    # Create user source directory
    try:
        logger.info("Create user source directory {}".format(_user_src))
        os.mkdir(_user_src)
    except FileExistsError:
        logger.info("{} already exists".format(_user_src))
    except PermissionError as e:
        logger.critical(e)
        sys.exit(-1)

    # setup ReportGenerator
    ReportGenerator.setup(_report_file)

    # Run server
    config = MinimalApplicationConfigurator()
    config.register(StaticsConfigurationComponent)
    controller = Controller(_user_src, _max_sessions, _max_sessions_per_addr)
    try:
        config.update_blueprint({
            'root_controller': controller,
            'renderers': ['genshi'],
            'default_renderer': 'genshi',
            'paths': {
                'static_files': 'web'
            }
        })
        logger.info("Listening on port " + str(_port) + ", host " + str(_host))

        serv = WebSocketsService(controller._sess_man, _ws_interface, _ws_port)
        serv.start()

        waitress.serve(config.make_wsgi_app(), host=_host, port=_port)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical("Catched Exception: " + str(e))
        logger.critical("Shutting down due to Exception")
    finally:
        try:
            logger.info("Stop WebSocketsService...")
            serv.stop()
        except Exception as e:
            logger.critical(str(e))
        try:
            logger.info("Shut down Controller...")
            controller.shutdown()
        except Exception as e:
            logger.critical(str(e))
