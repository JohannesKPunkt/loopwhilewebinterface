#  ArgParserTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import sys, unittest
import tests_common
from ArgParser import *

class ArgParserTests(unittest.TestCase):
    def test_illegal_args(self):
        #-b= instead of -b
        occurred = False
        try:
            parser = ArgParser(["--a", "-b=1", "--c=2"], ["--a", "-b", "--c="], True)
        except IllegalArgumentError:
            occurred = True
        self.assertTrue(occurred, "Expected Exception to be thrown.")
        
        #-b instead of -b=
        occurred = False
        try:
            parser = ArgParser(["--a", "-b", "--c=2"], ["--a", "-b=", "--c="], True)
        except IllegalArgumentError:
            occurred = True
        self.assertTrue(occurred, "Expected Exception to be thrown.")
        
        #unknown --c=
        occurred = False
        try:
            parser = ArgParser(["--a", "-b=1", "--c=2"], ["--a", "-b"], True)
        except IllegalArgumentError:
            occurred = True
        self.assertTrue(occurred, "Expected Exception to be thrown.")

        #unknown -foo=
        occurred = False
        try:
            parser = ArgParser(["--a", "-foo=bar", "-b"], ["--a", "-b"], True)
        except IllegalArgumentError:
            occurred = True
        self.assertTrue(occurred, "Expected Exception to be thrown.")

        #unknown -foo
        occurred = False
        try:
            parser = ArgParser(["--a", "-foo", "-b"], ["--a", "-b"], True)
        except IllegalArgumentError:
            occurred = True
        self.assertTrue(occurred, "Expected Exception to be thrown.")

    def test_no_exception(self):
        #-b= instead of -b
        parser = ArgParser(["--a", "-b=1", "--c=2"], ["--a", "-b", "--c="])
        
        #-b instead of -b=
        parser = ArgParser(["--a", "-b", "--c=2"], ["--a", "-b=", "--c="])
        
        #unknown --c=
        parser = ArgParser(["--a", "--c=2"], ["--a", "-b"])

        #unknown -foo=:
        parser = ArgParser(["--a", "-foo=bar", "-b"], ["--a", "-b"])

        #unknown -foo
        occurred = False
        parser = ArgParser(["--a", "-foo", "-b"], ["--a", "-b"])
        
        #it is legal not to use all possible options
        parser = ArgParser(["--a"], ["--a", "-b"], True)
        parser = ArgParser(["--a"], ["--a", "-b"])
        parser = ArgParser([], ["--a", "-b"], True)
        parser = ArgParser([], ["--a", "-b"])
        parser = ArgParser(["--a"], ["--a", "-otherarg="], True)
        parser = ArgParser(["--a"], ["--a", "-otherarg="])
        parser = ArgParser([], ["--a", "-otherarg"], True)
        parser = ArgParser([], ["--a", "-otherarg"])

        # all empty
        parser = ArgParser([], [])

    def test_getValue(self):
        parser = ArgParser(["--a", "--key=value", "--c=2"], ["--key=", "-b", "--c=", "--foo="])
        self.assertEqual(parser.get_value("--key"), "value")
        self.assertEqual(parser.get_value_default("--foo", "bar"), "bar")
        self.assertEqual(parser.get_value_default("--key", "thewrongvalue"), "value")

        parser = ArgParser(["--a", "--key=value", "--c=2", "-foo="], ["--key=", "-b", "--c=", "-foo="])
        self.assertEqual(parser.get_value("-foo"), "")

        parser = ArgParser(["--key=value", "a", "b=4", "-c=2", "-foo="], ["--key=", "b=", "-c=", "-foo=", "a"], True)
        self.assertEqual(parser.get_value("-foo"), "")
        self.assertEqual(parser.get_value("-c"), "2")
        self.assertEqual(parser.get_value("b"), "4")

        occurred = False
        try:
            parser.get_value("--doesnotexist=")
        except OptionNotFoundError:
            occurred = True
        self.assertTrue(occurred, "Expected Exception to be thrown.")

if __name__ == '__main__':
    unittest.main()
