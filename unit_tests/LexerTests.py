#  LexerTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import sys, unittest
from external_libs.lexer import Lexer, LexerError

class LexerTests(unittest.TestCase):
    def test_simple(self):
        rules = [
            ('\d+',             'NUMBER'),
            ('[a-zA-Z_]+',      'IDENTIFIER'),
            ('\+',              'PLUS'),
            ('\-',              'MINUS'),
            ('\*',              'MULTIPLY'),
            ('\/',              'DIVIDE'),
            ('\(',              'LP'),
            ('\)',              'RP'),
            ('=',               'EQUALS'),
        ]
        
        input_str = 'x  =\t2*(2y+z*z'

        l = Lexer(rules, skip_whitespace=True)
        l.input(input_str)
        print(input_str)
        expected = [('x', 'IDENTIFIER'), ('=', 'EQUALS'), ('2', 'NUMBER'), ('*', 'MULTIPLY'), ('(', 'LP'), ('2', 'NUMBER'), ('y', 'IDENTIFIER'),
            ('+', 'PLUS'), ('z', 'IDENTIFIER'), ('*', 'MULTIPLY'), ('z', 'IDENTIFIER')]
        for expected_token in expected:
            token = l.token()
            self.assertEquals(token.val, expected_token[0])
            self.assertEquals(token.type, expected_token[1])
        self.assertIsNone(l.token())
        
        l.input(input_str)
        i=0
        for token in l.tokens():
            expected_token = expected[i]
            self.assertEquals(token.val, expected_token[0])
            self.assertEquals(token.type, expected_token[1])
            i += 1
        self.assertEquals(i, len(expected))

    def test_no_match(self):
        rules = [
            ('\d+',             'NUMBER'),
            ('[a-zA-Z_]+',      'IDENTIFIER'),
            ('\+',              'PLUS'),
            ('\-',              'MINUS'),
            ('\*',              'MULTIPLY'),
            ('\/',              'DIVIDE'),
            ('\(',              'LP'),
            ('\)',              'RP'),
            ('=',               'EQUALS'),
        ]
        
        
        input_str = 'x  <= y'

        l = Lexer(rules, skip_whitespace=True)
        l.input(input_str)
        print(input_str)
        expected = [('x', 'IDENTIFIER')]
        for expected_token in expected:
            token = l.token()
            self.assertEqual(token.val, expected_token[0])
            self.assertEqual(token.type, expected_token[1])
        
        error_occurred = False
        try:
            token = l.token()
        except LexerError as err:
            error_occurred = True
            self.assertEqual(err.pos, 3)
        self.assertTrue(error_occurred)

