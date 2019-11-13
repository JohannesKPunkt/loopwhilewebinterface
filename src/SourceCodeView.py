#  SourceCodeView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module provides a generic class for displaying Loop/While code
#  in HTML

from external_libs.lexer import Lexer, LexerError


# Lexer rules that are used to provide basic syntax highlighting
_lexer_rules = [
    ('def|enddef|LOOP|WHILE|do|enddo|if|then|else|in|out|aux', 'KEYWORD'),
    ('loop|while',                                             'KEYWORD'),
    ('#',                                                      'HASHTAG'),
    ('\d+',                                                    'NUMBER'),
    ('[a-zA-Z_](\w|\d)*',                                      'IDENTIFIER'),
    ('\+|\-|\*|div|\%|==|<|<=|>|>=|!=',                        'OPERATOR'),
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
    ('\S',                                                     'ILLEGAL_SYMBOL'),
]

# The source code view generation can be highly customized by overriding
# the hook functions. Each of this functions returns a string as part of
# the generated HTML output. At the begin and the end of the generation,
# begin_view_hook() respectively end_view_hook() are called. Both shall
# enclose a <table></table>, for which each code line gets displayed as
# a row. The <tr> and </tr> tags for each row shall be generated by
# begin_row_hook() and end_row_hook(). The precise layout of the table
# itself is left completely to the caller.
class SourceCodeView:
    def begin_row_hook(self, linecount):
        pass

    def end_row_hook(self, linecount):
        pass

    def begin_view_hook(self):
        pass

    def end_view_hook(self):
        pass

    #
    #  name: getSourceCodeView
    #  @param
    #    source string with Loop/While source code to display
    #  @return a valid html <table>-tag that can be inserted into a XHTML template or file
    #
    def get_source_code_view(self, source):
        lexer = Lexer(_lexer_rules, False)
        lexer.input(source)

        linecount = 1
        in_comment = False
        output = self.begin_view_hook()
        output += self.begin_row_hook(linecount)

        for token in lexer.tokens():
            if token.type == 'LINEBREAK':
                linecount += 1
                output += self.end_row_hook(linecount-1) + self.begin_row_hook(linecount)
                in_comment = False
            elif token.type == 'ENTER_COMMENT' or in_comment:
                output += "<font color=\"#6f6564\" style=\"opacity:.8\">" + token.val + "</font>"
                in_comment = True
            elif token.type == 'NUMBER':
                output += "<font color=\"#d7432e\" style=\"opacity:.8\">" + token.val + "</font>"
            elif token.type == 'OPERATOR':
                output += "<font color=\"#d7910e\" style=\"opacity:.8\">" + token.val + "</font>"
            elif token.type in ('IDENTIFIER', 'LP', 'RP', 'SEMICOLON', 'COLON', 'ASSIGNMENT', 'ILLEGAL_SYMBOL'):
                output += "<font color=\"#F8FBEF\" style=\"opacity:.8\">" + token.val + "</font>"
            elif token.type == 'SPACE':
                output += "&nbsp;"
            elif token.type == 'HASHTAG':
                output += "#"
            elif token.type == 'TAB':
                output += "&nbsp;&nbsp;&nbsp;&nbsp;"
            elif token.type == 'KEYWORD' or token.type == 'BUILTIN':
                output += "<font color=\"#d7910e\" style=\"opacity:.8\">" + token.val + "</font>"
            else:
                raise RuntimeError("unknown token type: " + str(token))
        output += self.end_row_hook(linecount) + self.end_view_hook()
        return output
