LBRAC = "LBRAC"
RBRAC = "RBRAC"
STRING = "STRING"
WHITESPACE = "WHITESPACE"
COMMAND = "COMMAND"

_lexer_rules = [
    ('{',                                                      LBRAC),
    ('}',                                                      RBRAC),
    ('\s',                                                     WHITESPACE),
    ('\\\\(\w+)',                                              COMMAND),
    ('([\w,;\.:\-\+*/|<>~#\'"§$%\&\(\)=\?!]|\\\\)*',           STRING),
]

_token_map = {LBRAC: "'{'", RBRAC: "'}'", STRING: STRING, WHITESPACE: WHITESPACE, COMMAND: COMMAND}

from external_libs.lexer import Lexer, LexerError, Token
from ArgParser import ArgParser
from SourceCodeView import SourceCodeView

import Logging
import sys
import html
import traceback

logger = None

class ParserException(Exception):
    def __init__(self, pos, code, errmsg=None):
        escaped = code[max(0,pos-15): min(len(code), pos+15)].replace("\n", " ")
        escaped = escaped.replace("\r", " ").replace("\t", " ")
        msg  = "\nParserError for input: " + escaped + "\n"
        msg += "                       " + (min(15, pos)*" ") + "^"
        if errmsg is not None:
            msg += "\n" + errmsg
        super().__init__(msg)

EOF = StopIteration

class TutorialSourceCodeView(SourceCodeView):
    def begin_row_hook(self, linecount):
        return "<tr><td class=\"codeViewLineNo\">&nbsp;"\
               + str(linecount) + "&nbsp;</td>"\
               + "<td class=\"codeViewLine\">"

    def end_row_hook(self, linecount):
        return "</td></tr>\n"

    def begin_view_hook(self):
        return "<div class=\"codeViewDiv\">\n<table class=\"codeView\">\n"

    def end_view_hook(self):
        return ("<tr><td colspan=\"2\" class=\"codeViewLink\">\n<a href=\"\" onclick=\"set_editor_text('"
              + self._get_escaped_source()
              + "'); return false;\" class=\"codeViewLink\">&larr; load to editor</a>\n</td></tr>\n"
              + "</table>\n</div>\n")

    def _get_escaped_source(self):
        return html.escape(self.source).replace("\n", "\\n").replace("\r", "\\r")


class TutorialGenerator:
    def __init__(self):
        self.lexer = Lexer(_lexer_rules, False)
        self._it = None

        # A list of strings and placeholder objects of which the desired output
        # comprises. While processing the input, strings and placeholder objects
        # are inserted to the list. After this step, the placeholders are processed,
        # by calling its process(generator) method that has to return an output string.
        self._output = []
        self._input = None

        # A list of tuples (title, []) where the first component is the title
        # of a chapter and the second component a list of the titles of its sections.
        self.chapters = []
        self._headline_counter = 0

    class TableOfContentsPlaceholder:
        def process(self, generator):
            counter = 0
            table = "<h2>Inhaltsverzeichnis</h2>\n"
            for chapter in generator.chapters:
                table += ("<a href=\"#headline" + str(counter) + "\">"
                          + chapter[0] + "</a><br />\n")
                counter += 1
                for section in chapter[1]:
                    table += ("&nbsp;&nbsp;" + "<a href=\"#headline"
                              + str(counter) + "\">" + section + "</a><br />\n")
                    counter += 1
            return table

    def _raise_parse_exception(self, pos, errmsg=None):
        raise ParserException(pos, self._input, errmsg)

    def _next_token_or_eof(self):
        try:
            token = self._it.__next__()
            return token
        except StopIteration:
            return EOF

    # Returns next token, skips whitespaces (if set) and raises Exception if the 
    # next non-whitespace token is not of type expected_type (if specified) or EOF.
    def _next_token(self, expected_type = None, skip_whitespaces = True):
        token = self._next_token_or_eof()
        while token != EOF and skip_whitespaces and token.type == WHITESPACE:
            token = self._next_token_or_eof()
        if token == EOF:
            self._raise_parse_exception(max(len(self._input)-1, 0), "unexpected EOF")
        elif expected_type is not None and token.type != expected_type:
            self._raise_parse_exception(token.pos, "expected token of type " + _token_map[expected_type]
                                                   + " got " 
                                                   + (_token_map[token.type] if token.type != STRING else "\"" + token.val + "\"")
                                                   + " instead.")
        return token

    # Consumes arbitrary many STRING or WHITESPACE tokens until a token 
    # of stop_type occurrs. Skips leading and trailing whitespaces if
    # parameter skip is set to True.
    # Raises Exception in case of EOF or other token type.
    def _consume_until(self, stop_type, skip=True):
        token = self._next_token(skip_whitespaces = skip)
        string = ""
        trailing_whitespaces = ""
        while True:
            if token.type == STRING or (not skip and token.type == WHITESPACE):
                string += trailing_whitespaces
                string += token.val
                trailing_whitespaces = ""
            elif skip and token.type == WHITESPACE:
                trailing_whitespaces += token.val
            elif token.type == stop_type:
                return string
            else:
                self._raise_parse_exception(max(len(self._input)-1, 0),
                                            "expected string sequence terminated by token of type " + _token_map[stop_type]
                                            + ", got " + _token_map[token.type] + " instead.")
            token = self._next_token(skip_whitespaces = False)

    # Parses the input description file, generates the HTML code and returns it as a string
    def generate(self, input_str):
        try:
            self._input = input_str
            self.lexer.input(input_str)
            self._it = self.lexer.tokens()
            self._it.__iter__()
            token = self._next_token_or_eof()
            while token != EOF:
                if token.type == COMMAND:
                    if   token.val == "\\headline":
                        self._command_headline()
                    elif token.val == "\\subhead":
                        self._command_subhead()
                    elif token.val == "\\code":
                        self._command_code()
                    elif token.val == "\\chapter":
                        self._command_chapter()
                    elif token.val == "\\section":
                        self._command_section()
                    elif token.val == "\\linebreak":
                        self._command_linebreak()
                    elif token.val == "\\link":
                        self._command_link()
                    elif token.val == "\\bold":
                        self._command_bold()
                    elif token.val == "\\italic":
                        self._command_italic()
                    elif token.val == "\\tableofcontents":
                        self._command_tableofcontents()
                    elif token.val == "\\html":
                        self._command_html()
                    else:
                        self._raise_parse_exception(token.pos, "invalid command token: \"" + token.val + "\"")
                elif token.type == WHITESPACE:
                    pass
                elif token.type == STRING:
                    self._output.append(html.escape(token.val))
                else:
                    self._raise_parse_exception(token.pos, "expected command token")
                token = self._next_token_or_eof()
        except LexerError as e:
            self._raise_parse_exception(e.pos, "invalid token")

        out_str = ""
        need_whitespace = False
        for entry in self._output:
            if isinstance(entry, str):
                if need_whitespace:
                        out_str += " "
                out_str += entry
                need_whitespace = True if out_str[-1] != "\n" else False
            else:
                out_str += entry.process(self)
                need_whitespace = False
        return out_str


    def _command_headline(self):
        self._next_token(LBRAC)
        self._output.append("<h1>" + html.escape(self._consume_until(RBRAC)) + "</h1>\n")

    def _command_subhead(self):
        self._next_token(LBRAC)
        self._output.append("<h2>" + html.escape(self._consume_until(RBRAC)) + "</h2>\n")

    def _command_chapter(self):
        self._next_token(LBRAC)
        title = str(len(self.chapters)+1) + ". " + html.escape(self._consume_until(RBRAC))
        self.chapters.append((title, []))
        self._output.append("<h2 id=\"headline" + str(self._headline_counter)
                            + "\">" + title + "</h2>\n")
        self._headline_counter += 1

    def _command_section(self):
        self._next_token(LBRAC)
        title = html.escape(self._consume_until(RBRAC))
        try:
            chapter = self.chapters[-1]
        except IndexError:
            raise Exception("section needs a surrounding chapter.")
        title = str(len(self.chapters)) + "." + str(len(chapter[1])+1) + ". " + title
        chapter[1].append(title)
        self._output.append("<h3 id=\"headline" + str(self._headline_counter)
                            + "\">" + title + "</h3>\n")
        self._headline_counter += 1

    def _command_code(self):
        self._next_token(LBRAC)
        code = self._consume_until(RBRAC)
        self._output.append(TutorialSourceCodeView().get_source_code_view(code) + "\n")

    def _command_link(self):
        self._next_token(LBRAC)
        link_target = html.escape(self._consume_until(RBRAC))
        self._next_token(LBRAC)
        link_text = html.escape(self._consume_until(RBRAC))
        self._output.append("<a href=\"" + link_target + "\">" + link_text + "</a>")

    def _command_text(self):
        self._next_token(LBRAC)
        self._output.append(html.escape(self._consume_until(RBRAC, False)) + "\n")

    def _command_bold(self):
        self._next_token(LBRAC)
        self._output.append("<b>" + html.escape(self._consume_until(RBRAC)) + "</b>")

    def _command_italic(self):
        self._next_token(LBRAC)
        self._output.append("<i>" + html.escape(self._consume_until(RBRAC)) + "</i>")

    def _command_linebreak(self):
        self._output.append("<br/>\n")

    def _command_tableofcontents(self):
        self._output.append(self.TableOfContentsPlaceholder())

    def _command_html(self):
        self._next_token(LBRAC)
        self._output.append(self._consume_until(RBRAC))

if __name__ == '__main__':
    try:
        arg_parser = ArgParser(sys.argv[1:], ["--infile=", "--outfile=", "--loglevel=", "--logfile"], True)
        # Prepare logging
        _loglevel = arg_parser.get_value_default("--loglevel", "INFO")
        _logfile = arg_parser.get_value_default("--logfile", None)
        Logging.set_global_options(_loglevel, _logfile)
        logger = Logging.get_logger(__name__)
    except Exception as e:
        print("Exception while parsing arguments: " + str(e))
        sys.exit(-1)

    generator = TutorialGenerator()
    infile_path = arg_parser.get_value("--infile")
    outfile_path = arg_parser.get_value("--outfile")

    with open(infile_path, "r") as input_file:
        input_str = input_file.read()

    try:
        output_str = generator.generate(input_str)
        with open(outfile_path, "w") as output_file:
            output_file.write("<div>\n");
            output_file.write(output_str)
            output_file.write("<br/><br/>\n</div>\n");
    except ParserException as e:
        logger.error(traceback.format_exc())
