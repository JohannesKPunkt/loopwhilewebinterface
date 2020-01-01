#  Main.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#
#

from wsgiref.simple_server import make_server
from tg import MinimalApplicationConfigurator
from tg.configurator.components.statics import StaticsConfigurationComponent

import sys

import Logging
from ArgParser import ArgParser

_host = None
_port = None
logger = None

if __name__ == '__main__':
    # Process arguments
    try:
        arg_parser = ArgParser(sys.argv[1:], ["--host=", "--port=", "--loglevel=",
            "--logfile=", "--user_src=", "--max_sessions="], True)
        _host = arg_parser.get_value_default("--host", "127.0.0.1")
        _port = int(arg_parser.get_value_default("--port", "8080"))
        _loglevel = arg_parser.get_value_default("--loglevel", "INFO")
        _logfile = arg_parser.get_value_default("--logfile", None)
        _user_src = arg_parser.get_value_default("--user_src", "./user_src")
        _max_sessions = int(arg_parser.get_value_default("--max_sessions", "200"))
    except Exception as e:
        print("Exception while parsing arguments: " + str(e))
        sys.exit(-1)

    # Prepare logging
    Logging.set_global_options(_loglevel, _logfile)
    logger = Logging.get_logger(__name__)


from Controller import Controller

if __name__ == '__main__':
    # Run server
    config = MinimalApplicationConfigurator()
    config.register(StaticsConfigurationComponent)
    controller = Controller(_user_src, _max_sessions)
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
        httpd = make_server(_host, _port, config.make_wsgi_app())
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical("Catched Exception: " + str(e))
        logger.critical("Shutting down due to Exception")
    finally:
        controller.shutdown()
