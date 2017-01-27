#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from raffaello.src.raffaello import Raffaello
from raffaello.src.raffaello import Commission

class RaffaelloTest(unittest.TestCase):

    def test_color_red(self):
        request = '''
this=>red
'''
        c = Commission(request)
        line = 'this should be in red and This not'

        expected = '\x1b[31mthis\x1b[0m should be in red and This not'
        
        raf = Raffaello(c.commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)


    def test_regex_pattern(self):
        request = '''
[tT]his=>red
'''
        c = Commission(request)
        line = 'this should be in red and This too'

        expected = '\x1b[31mthis\x1b[0m should be in red and \x1b[31mThis\x1b[0m too'
        
        raf = Raffaello(c.commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)


    

