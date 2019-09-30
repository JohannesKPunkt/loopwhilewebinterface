#  InterpreterView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module enables separation of the interpreter view generation and the
#  debugger functionality itself.

from genshi.core import Markup

class InterpreterView(dict):
    def __init__(self):
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
