#  DebuggerView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module enables separation of the debugger view generation and the
#  debugger functionality itself.


from lexer import Lexer

_lexer_rules = [
    ('\d+',                                                    'NUMBER'),
    ('[a-zA-Z_]\w+',                                           'IDENTIFIER'),
    ('\+|\-|\*|div|\%|==|<|<=|>|>=',                           'OPERATOR'),
    ('\(',                                                     'LP'),
    ('\)',                                                     'RP'),
    (';',                                                      'SEMICOLON'),
    ('def|enddef|loop|while|do|enddo|if|then|else|in|out|aux', 'KEYWORD'),
    ('succ|pred',                                              'BUILTIN'),
    (':=',                                                     'ASSIGNMENT'),
    (',|:',                                                    'COLON'),
    (' ',                                                   'SPACE'),
    ('\t',                                                     'TAB'),
    ('\n|\r\n',                                                'LINEBREAK'),
    ('//',                                                     'ENTER_COMMENT'),
]

source_code_view_prefix = """<html>
<head>
</head>
    <body>
        <script>
            function setBullet(id)
            {
                 var elem = document.getElementById(id);
                 if (elem.getAttribute("src") == "/img/transparentdot.png")
                 {
                     elem.setAttribute("src", "/img/reddot.png");
                 }
                 else
                 {
                     elem.setAttribute("src", "/img/transparentdot.png");
                 }
            }
        </script>
        <style>
        .debuggerCodeView { background-color:#151515;border-collapse:collapse;color: #F8FBEF;font-size:12px;}
        .debuggerCodeView td, .myOtherTable th { padding:0px;border:0; }
        .debuggerCodeViewLineNo { background-color:#2E2E2E; text-align: right;}
        .debuggerCodeViewSide { background-color:#2E2E2E; padding: 15px;}
        </style>
        <div style="background-color:#151515; color:#F8FBEF; opacity: 45%; padding-left: 0px; max-height: 70%;overflow:scroll;">"""

source_code_view_suffix = """        </div>
    </body>
</html>"""

#  
#  name: getSourceCodeView
#  @param
#    source string with Loop/While source code to display
#    highlight_line line number that shall be highlighted (default=-1 means no line will be highlighted)
#  @return a valid html <table>-tag that can be inserted into the debugger.xhtml template
#  
def getSourceCodeView(source, highlight_line=6):#TODO replace 6 with -1
    lexer = Lexer(_lexer_rules, False)
    lexer.input(source)
    
    linecount = 1
    in_comment = False
    output = "<table class=\"debuggerCodeView\">"
    output += "<tr><td class=\"debuggerCodeViewLineNo\">&nbsp;1</td>" \
              + "<td class=\"debuggerCodeViewSide\" onclick=\"setBullet(&quot;dot1&quot;);\" >" \
              + "&nbsp;<img src=\"/img/transparentdot.png\" width=\"10em\" length=\"10em\" id=\"dot1\"/>&nbsp;"\
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
                      + "&nbsp;<img src=\"/img/transparentdot.png\" width=\"10em\" length=\"10em\" id=\"dot"\
                      + str(linecount) + "\" onclick=\"setBullet(&quot;dot"\
                      + str(linecount) + "&quot;);\" />&nbsp;</td><td" + bgcolor_str + ">"
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
    return source_code_view_prefix + output + source_code_view_suffix
