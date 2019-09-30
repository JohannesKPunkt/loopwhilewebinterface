#  ArgParser.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import Logging
logger = Logging.get_logger(__name__)

class ArgParser:
    def __init__(self, args, known_options, abort_unknown=False):
        self._args = args
        for arg in self._args:
            equals_pos = arg.find("=")
            shortened = arg
            if equals_pos != -1:
                shortened = arg[:equals_pos+1]
            if shortened not in known_options:
                if abort_unknown:
                    raise(IllegalArgumentError("unknown option \"" + arg + "\""))
                else:
                    logger.warning("ignoring unknown option \"" + arg + "\"")

    # returns the value that is assigned to a certain option, e.g.
    # if the user set --foo=bar, getValue("--foo") returns "bar"
    def get_value(self, name):
        for arg in self._args:
            equals_pos = arg.find("=")
            shortened = arg
            if equals_pos != -1:
                shortened = arg[:equals_pos+1]
            else:
                continue
            if shortened[:len(shortened)-1] == name:
                return arg[equals_pos+1:]
        raise OptionNotFoundError("Value for option " + name + " not found")

    def get_value_default(self, name, default):
        try:
            return self.get_value(name)
        except OptionNotFoundError:
            return default


class IllegalArgumentError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class OptionNotFoundError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


