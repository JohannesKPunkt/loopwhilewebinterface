#  ReportGenerator.py
#  
#  Copyright 2020 Johannes Kern <johannes.kern@fau.de>
#
#
#  This module is used to generate user statistics

import logging
import logging.handlers
import sys
from datetime import datetime

from external_libs.lexer import Lexer, LexerError, Token
from ArgParser import ArgParser

_report_logger = None

_lexer_rules = [
    ('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d',               "DATETIME"),
    ('([\w,;\.:\-\+*/|<>~#\'"§$%\&\(\)=\?!\[\]])+',            "STRING"),
]

HLINE = "======================================================="

def setup(filename="report_data.log"):
    global _report_logger
    _report_logger = logging.getLogger("ReportGenerator")
    handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1024*1024, backupCount=1)
    formatter = logging.Formatter("%(asctime)-15s #%(message)s")
    handler.setFormatter(formatter)
    _report_logger.addHandler(handler)
    _report_logger.setLevel("INFO")

def logSessionBegin(client_address, session_id):
    _report_logger.info("SESSION_BEGIN client_address: " + client_address + " session_id: " + session_id)

def logSessionEnd(client_address, session_id):
    _report_logger.info("SESSION_END client_address: " + client_address + " session_id: " + session_id)


# A class to generate a histogram. Used by different metrics in this file.
class Histogram:
    def __init__(self):
        self.data_map = {}

    def increment(self, key):
        if key not in self.data_map:
            self.data_map[key] = 1
        else:
            self.data_map[key] += 1

    def printHistogram(self, width, print_sorted=False):
        max_val = max(self.data_map.values())
        max_keylen = 0
        for k in self.data_map.keys():
            max_keylen = max(max_keylen, len(str(k)))

        items = self.data_map.items()
        if print_sorted:
            items = sorted(items)

        for k, v in items:
            line = str(k)
            for _ in range(0, max_keylen - len(line)):
                line += " "
            line += ":"
            number_of_bars = round(v*width/float(max_val))
            for _ in range(0, number_of_bars):
                line += "|"
            for _ in range(0, width - number_of_bars):
                line += " "
            line += " (" + str(v) + " times)"
            print(line)

# This metric determines the maximal number of concurrent sessions of each
# user. Only connections from the same address on the same day are treated
# as the same user.
class ConcurrentSessionsPerAddress:
    def __init__(self):
        self.max = 0

        # maps addresses to number of active sessions
        self._map = {}

        # maps addresses to maximum of active sessions
        self._max_map = {}

        self._histogram = Histogram()
        self._last_event = datetime.fromtimestamp(0).date()

    def _transfer_to_histogram(self):
        for k, v in self._max_map.items():
            self._histogram.increment(v)
        self._max_map = {}

    def reportSessionBegin(self, time, client_address, session_id):
        if self._last_event < time.date():
            self._transfer_to_histogram()
        self._last_event = time.date()

        if client_address not in self._map:
            self._map[client_addr] = 1
        else:
            self._map[client_addr] += 1

        cur = self._map[client_addr]
        if cur > self.max:
            self.max = cur
        self._max_map[client_addr] = max(self._max_map.get(client_addr, 0), cur)

    def reportSessionEnd(self, time, client_address, session_id):
        self._map[client_addr] -= 1

    def printReport(self):
        self._transfer_to_histogram()
        print("Maximal number of concurrent active sessions: " + str(self.max))
        print("Histogram:")
        self._histogram.printHistogram(20, True)


# This metric evaluates the length of each session
class SessionDuration:
    def __init__(self):
        # maps session_ids to begin time
        self._map = {}

        self.avg = 0
        self.count = 0
        self._histogram = Histogram()

    def get_category(self, duration):
        if duration < 60:
            return " " + str((duration//10)*10) + " to " + str(((duration//10)+1)*10) + " sec"
        else:
            return str((duration//60)) + " minutes"

    def reportSessionBegin(self, time, client_address, session_id):
        self._map[session_id] = time

    def reportSessionEnd(self, time, client_address, session_id):
        try:
            begin = self._map[session_id]
            diff = time.timestamp() - begin.timestamp()
            self.avg = (self.avg*self.count + diff)/(self.count+1)
            self.count += 1
            cat = self.get_category(diff)
            self._histogram.increment(cat)
        except KeyError:
            print("WARN: SESSION_END without corresponding SESSION_BEGIN (session_id=" + str(session_id) + ")")

    def printReport(self):
        print("Average Session duration: " + str(self.avg) + " sec")
        print("Histogram:")
        self._histogram.printHistogram(20, True)


# This metric counts the total number of sessions for each address.
# Should be used with care since the number of client addresses might
# be huge.
class SessionsPerAddress:
    def __init__(self):
        self._histogram = Histogram()

    def reportSessionBegin(self, time, client_address, session_id):
        self._histogram.increment(client_address)

    def reportSessionEnd(self, time, client_address, session_id):
        pass

    def printReport(self):
        print("Total sessions per address: ")
        self._histogram.printHistogram(20, True)


def consume_token(lexer, type):
    token = lexer.token()
    if token.type != type:
        raise RuntimeError("Expected token of type \"" + type + "\", got " + str(token) + " instead.")
    return token.val

if __name__ == "__main__":
    arg_parser = ArgParser(sys.argv[1:], ["--infile="], True)
    filename = arg_parser.get_value("--infile")

    lexer = Lexer(_lexer_rules)
    metrics = [ConcurrentSessionsPerAddress(), SessionDuration(), SessionsPerAddress()]

    with open(filename, "r") as infile:
        for line in infile:
            lexer.input(line)
            time_str = consume_token(lexer, "DATETIME")
            time = datetime.strptime(time_str + "000", "%Y-%m-%d %H:%M:%S,%f")

            typestr = consume_token(lexer, "STRING")
            if typestr == "#SESSION_BEGIN":
                consume_token(lexer, "STRING")
                client_addr = consume_token(lexer, "STRING")
                consume_token(lexer, "STRING")
                session_id = consume_token(lexer, "STRING")
                for metric in metrics:
                    metric.reportSessionBegin(time, client_addr, session_id)
            elif typestr == "#SESSION_END":
                consume_token(lexer, "STRING")
                client_addr = consume_token(lexer, "STRING")
                consume_token(lexer, "STRING")
                session_id = consume_token(lexer, "STRING")
                for metric in metrics:
                    metric.reportSessionEnd(time, client_addr, session_id)
            else:
                print("WARN: illegal type: " + typestr)

        print(HLINE)
        for metric in metrics:
            metric.printReport()
            print(HLINE)
