#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from raffaello.src.raffaello import Raffaello
from raffaello.src.raffaello import parse_request


class RaffaelloTest(unittest.TestCase):
    '''Raffaello test class'''

    def test_color_red(self):
        '''Test highlight word'''
        request = '''
this=>red
'''
        line = 'this should be in red and This not'
        expected = '\x1b[31mthis\x1b[0m should be in red and This not'

        raf = Raffaello(parse_request(request))
        result = raf.paint(line)
        self.assertEqual(expected, result)

    def test_regex_pattern(self):
        '''Test highlight matching strings'''
        request = '''
[tT]his=>red
another=>green
'''
        line = 'this should be in red and This too'

        expected = '\x1b[31mthis\x1b[0m should be in red and \x1b[31mThis\x1b[0m too'

        raf = Raffaello(parse_request(request))
        result = raf.paint(line)
        self.assertEqual(expected, result)

    def test_blind(self):
        '''Test cancel matching string'''
        request = '''
do_not_show_this=>blind
show_this=>red
'''
        line = 'generic text'
        expected = 'generic text'

        commission = parse_request(request)
        raf = Raffaello(commission)

        result = raf.paint(line)
        self.assertEqual(expected, result)

        line = 'do_not_show_this'
        expected = None

        raf = Raffaello(commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)

        line = 'do_not_show_this together with other text'
        expected = None

        raf = Raffaello(commission)
        result = raf.paint(line)
        self.assertEqual(expected, result)

    def test_paint_match_only(self):
        '''Test highlight only matching text'''

        request = '''
only=>red
another_match=>red
'''
        commission = parse_request(request)

        line = 'This line contains "only" and will be painted'
        expected = 'This line contains "\x1b[31monly\x1b[0m" and will be painted'
        raf = Raffaello(commission, match_only=True)
        result = raf.paint(line)
        self.assertEqual(expected, result)

        line = 'This line does not and won\'t be painted'
        expected = None
        raf = Raffaello(commission, match_only=True)
        result = raf.paint(line)
        self.assertEqual(expected, result)
