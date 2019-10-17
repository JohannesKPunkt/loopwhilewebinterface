#  InterpreterView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module enables separation of the interpreter view generation and the
#  debugger functionality itself.

from genshi.core import Markup

_DEFAULT_PROGRAM_CODE = \
"""// Hier könnte Ihr Programm stehen
in: i0
out: o0

o0 := 42 * i0;
"""

class InterpreterView(dict):
    def __init__(self, program_code):
        if program_code is not None:
            self["program_code"] = program_code
        else:
            self["program_code"] = _DEFAULT_PROGRAM_CODE

        self["title"] = "Loop/While interactive interpreter"
        self["text_before"] = Markup("<h1>LoopWhile interactive interpreter</h1>")
        self["includes_head"] = ["ace_style.xml"]
        self["includes_body"] = [
            "interpreter_text.html",
            "editor_container.xml",
            "controller_script.xml",
            "form_container.xml",
            "terminal.xml",
        ]
        self["debug_mode_button"] = "enter debug mode"
