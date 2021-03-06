#  SourceCodeView.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module provides a generic class for displaying Loop/While code
#  in HTML

from external_libs.lexer import Lexer, LexerError

import html


# Lexer rules that are used to provide basic syntax highlighting
_lexer_rules = [
    ('def|enddef|LOOP|WHILE|do|enddo|if|then|else|in|out|aux', 'KEYWORD'),
    ('loop|while|div|mod|endif',                               'KEYWORD'),
    ('#',                                                      'HASHTAG'),
    ('\d+',                                                    'NUMBER'),
    ('[a-zA-Z_](\w|\d)*',                                      'IDENTIFIER'),
    ('\+|\-|\*|==|<|<=|>|>=|!=',                               'OPERATOR'),
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

# This class addresses the issue, that words containing a keyword will be
# tokenized into several tokens, due to the explicit whitespace handling
# needed for correct indentation.
class Tokenizer:
    def __init__(self, source):
        lexer = Lexer(_lexer_rules, False)
        lexer.input(source)
        self._it = lexer.tokens()

    def __iter__(self):
        self._it.__iter__()
        self._cur_token = self._process_next_token()
        return self

    def _process_next_token(self):
        try:
            return self._it.__next__()
        except StopIteration:
            return None

    def __next__(self):
        if self._cur_token is None:
            raise StopIteration
        next_token = self._process_next_token()
        while next_token is not None and (
                self._cur_token.type in ('KEYWORD', 'BUILTIN', 'IDENTIFIER') and
                next_token.type in ('KEYWORD', 'BUILTIN', 'IDENTIFIER')):
            self._cur_token.val += next_token.val
            self._cur_token.type = 'IDENTIFIER'
            next_token = self._process_next_token()
        curToken = self._cur_token
        self._cur_token = next_token
        return curToken


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
        self.source = source

        linecount = 1
        in_comment = False
        output = self.begin_view_hook()
        output += self.begin_row_hook(linecount)

        for token in Tokenizer(source):
            if token.type == 'LINEBREAK':
                linecount += 1
                output += self.end_row_hook(linecount-1) + self.begin_row_hook(linecount)
                in_comment = False
            elif token.type == 'ENTER_COMMENT' or in_comment:
                output += "<span class=\"codeViewComment\">" + html.escape(token.val) + "</span>"
                in_comment = True
            elif token.type == 'NUMBER':
                output += "<span class=\"codeViewNumber\">" + html.escape(token.val) + "</span>"
            elif token.type == 'OPERATOR':
                output += "<span class=\"codeViewOperator\">" + html.escape(token.val) + "</span>"
            elif token.type in ('IDENTIFIER', 'LP', 'RP', 'SEMICOLON', 'COLON', 'ASSIGNMENT', 'ILLEGAL_SYMBOL'):
                output += "<span class=\"codeViewText\">" + html.escape(token.val) + "</span>"
            elif token.type == 'SPACE':
                output += "&nbsp;"
            elif token.type == 'TAB':
                output += "&nbsp;&nbsp;&nbsp;&nbsp;"
            elif token.type == 'BUILTIN':
                output += "<span class=\"codeViewBuiltin\">" + html.escape(token.val) + "</span>"
            elif token.type in ('KEYWORD', 'HASHTAG'):
                output += "<span class=\"codeViewKeyword\">" + html.escape(token.val) + "</span>"
            else:
                raise RuntimeError("unknown token type: " + str(token))
        output += self.end_row_hook(linecount) + self.end_view_hook()
        return output
