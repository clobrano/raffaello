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

    
    def test_blind(self):
        request = '''
do_not_show_this=>blind
'''
        c = Commission(request)

        line = 'generic text'
        expected = 'generic text'
        
        raf = Raffaello(c.commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)


        line = 'do_not_show_this'
        expected = None
        
        raf = Raffaello(c.commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)

        line = 'do_not_show_this together with other text'
        expected = None
        
        raf = Raffaello(c.commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)

