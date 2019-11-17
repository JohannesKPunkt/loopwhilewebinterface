#  DebuggerView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module enables separation of the debugger view generation and the
#  debugger functionality itself.


from external_libs.lexer import Lexer, LexerError
from SourceCodeView import SourceCodeView

from genshi.core import Markup
import Logging

logger = Logging.get_logger(__name__)

class DebuggerSourceCodeView(SourceCodeView):
    def begin_row_hook(self, linecount):
        return "<tr><td class=\"debuggerCodeViewLineNo\">&nbsp;"\
               + str(linecount) + "</td>"\
               + "<td class=\"debuggerCodeViewSide\">"\
               + "&nbsp;<img src=\"/img/transparentdot.png\" width=\"10px\" length=\"10px\" id=\"dot"\
               + str(linecount) + "\" onclick=\"breakpoint_action(&quot;dot"\
               + str(linecount) + "&quot;);\" />&nbsp;</td><td id=\"line" + str(linecount)+ "\">"

    def end_row_hook(self, linecount):
        return "</td></tr>"

    def begin_view_hook(self):
        return "<table class=\"debuggerCodeView\">"

    def end_view_hook(self):
        return "<tr style=\"height:100%;\"><td class=\"debuggerCodeViewLineNo\"></td><td class=\"debuggerCodeViewSide\"></td><td></td></tr></table>"


class DebuggerView(dict):
    def __init__(self, code, session_id = -1, tut_scrollbar_pos=0):
        self["title"] = "Loop/While interactive debugger"
        self["includes_head"] = ["ace_style.xml"]
        self["includes_body"] = [
            "debugger_container.xml",
            "controller_script.xml",
            "terminal.xml",
            "debugger_varview.xml"]
        self["current_mode"] = "debugger"
        try:
            self["debugger_view_content"] = Markup(DebuggerSourceCodeView().get_source_code_view(code))
        except LexerError as e:
            escaped = code[max(0,e.pos-10): min(len(code), e.pos+10)].replace("\n", " ")
            escaped = escaped.replace("\r", " ").replace("\t", " ")
            logger.info("LexerError for user input: " + escaped)
            logger.info("                           " + (min(10, e.pos)*" ") + "^")
            raise e
        self["session_id"] = session_id
        self["program_code"] = code
        self["tutorial_scrollbar_position"] = tut_scrollbar_pos
