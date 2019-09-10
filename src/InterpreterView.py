#  InterpreterView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module enables separation of the interpreter view generation and the
#  debugger functionality itself.

class InterpreterView(dict):
    def __init__(self):
        self["title"] = "Loop/While interactive interpreter"
        self["text_before"] = "<h1>LoopWhile interactive interpreter</h1>="
