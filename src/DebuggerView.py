#  DebuggerView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module enables separation of the debugger view generation and the
#  debugger functionality itself.


from external_libs.lexer import Lexer, LexerError

from genshi.core import Markup
import Logging

logger = Logging.get_logger(__name__)

# Lexer rules that are used to provide basic syntax highlighting
_lexer_rules = [
    ('def|enddef|loop|while|do|enddo|if|then|else|in|out|aux', 'KEYWORD'),
    ('\d+',                                                    'NUMBER'),
    ('[a-zA-Z_](\w|\d)*',                                      'IDENTIFIER'),
    ('\+|\-|\*|div|\%|==|<|<=|>|>=',                           'OPERATOR'),
    ('\(',                                                     'LP'),
    ('\)',                                                     'RP'),
    (';',                                                      'SEMICOLON'),
    ('succ|pred',                                              'BUILTIN'),
    (':=',                                                     'ASSIGNMENT'),
    (',|:',                                                    'COLON'),
    (' ',                                                      'SPACE'),
    ('\t',                                                     'TAB'),
    ('\n|\r\n',                                                'LINEBREAK'),
    ('//',                                                     'ENTER_COMMENT'),
]


class DebuggerView(dict):
    def __init__(self, code, session_id = -1):
        self["title"] = "Loop/While interactive debugger"
        self["includes_head"] = ["ace_style.xml"]
        self["includes_body"] = [
            "interpreter_text.html",
            "form_container.xml",
            "debugger_container.xml",
            "controller_script.xml",
            "terminal.xml",
            "debugger_varview.xml"]
        self["current_mode"] = "debugger"
        try:
            self["debugger_view_content"] = Markup(DebuggerView._get_source_code_view(code))
        except LexerError as e:
            escaped = code[max(0,e.pos-10): min(len(code), e.pos+10)].replace("\n", " ")
            escaped = escaped.replace("\r", " ").replace("\t", " ")
            logger.info("LexerError for user input: " + escaped)
            logger.info("                           " + (min(10, e.pos)*" ") + "^")
            raise e
        self["session_id"] = session_id

    #  
    #  name: getSourceCodeView
    #  @param
    #    source string with Loop/While source code to display
    #    highlight_line line number that shall be highlighted (default=-1 means no line will be highlighted)
    #  @return a valid html <table>-tag that can be inserted into the debugger.xhtml template
    #  
    @staticmethod
    def _get_source_code_view(source, highlight_line=-1):
        lexer = Lexer(_lexer_rules, False)
        lexer.input(source)
        
        linecount = 1
        in_comment = False#TODO: refactor redundant code
        output = "<table class=\"debuggerCodeView\">"
        output += "<tr><td class=\"debuggerCodeViewLineNo\">&nbsp;1</td>" \
                  + "<td class=\"debuggerCodeViewSide\" onclick=\"breakpoint_action(&quot;dot1&quot;);\" >" \
                  + "&nbsp;<img src=\"/img/transparentdot.png\" width=\"10px\" length=\"10px\" id=\"dot1\"/>&nbsp;"\
                  + "</td><td>"
        
        for token in lexer.tokens():
            if token.type == 'LINEBREAK':
                linecount += 1
                if highlight_line == linecount:
                    bgcolor_str = " style=\"background-color: #787878;\""
                else:
                    bgcolor_str = ""
                output += "</td></tr><tr><td class=\"debuggerCodeViewLineNo\">&nbsp;"\
                          + str(linecount) + "</td>"\
                          + "<td class=\"debuggerCodeViewSide\">"\
                          + "&nbsp;<img src=\"/img/transparentdot.png\" width=\"10px\" length=\"10px\" id=\"dot"\
                          + str(linecount) + "\" onclick=\"breakpoint_action(&quot;dot"\
                          + str(linecount) + "&quot;);\" />&nbsp;</td><td id=\"line" + str(linecount)+ "\"" + bgcolor_str + ">"
                in_comment = False
            elif token.type == 'ENTER_COMMENT' or in_comment:
                output += "<font color=\"#6f6564\" style=\"opacity:.8\">" + token.val + "</font>"#TODO font
                in_comment = True
            elif token.type == 'NUMBER':
                output += "<font color=\"#d7432e\" style=\"opacity:.8\">" + token.val + "</font>"
            elif token.type == 'OPERATOR':
                output += "<font color=\"#d7910e\" style=\"opacity:.8\">" + token.val + "</font>"
            elif token.type in ('IDENTIFIER', 'LP', 'RP', 'SEMICOLON', 'COLON', 'ASSIGNMENT'):
                output += "<font color=\"#F8FBEF\" style=\"opacity:.8\">" + token.val + "</font>"
            elif token.type == 'SPACE':
                output += "&nbsp;"
            elif token.type == 'TAB':
                output += "&nbsp;&nbsp;&nbsp;&nbsp;"
            elif token.type == 'KEYWORD' or token.type == 'BUILTIN':
                output += "<font color=\"#d7910e\" style=\"opacity:.8\">" + token.val + "</font>"
            else:
                raise RuntimeError("unknown token type: " + str(token))
        output += "</td></tr></table>"
        return output
