#!/usr/bin/env python
#import unittest
#import subprocess
#import os
#import raffaello
#from time import sleep
#
#class ConfigurationTest(unittest.TestCase):
#    def testParseColorOption(self):
#        colorOption = raffaello.parse_color_option("OK=>green error=>red warning=>yellow")
#        expectedColorOption = r"[{'OK': green}, {'error': red}, {'warning': yellow}]"
#
#        self.assertEqual(expectedColorOption, str(colorOption))
#
#class FunctionalTest(unittest.TestCase):
#
#
#    def testPaintWithInLineConfig(self):
#        testString = "[1234.5678] error message"
#        refString = "\x1b[32m[1234.5678]\x1b[39m error message"
#
#        colorOption = raffaello.parse_color_option("^\[.*?\]=>green")
#        coloredLine = raffaello.paint(testString, colorOption)
#        self.assertEqual(coloredLine, refString)
#
#
#    def testPaintWithConfig(self):
#        # Dmesg test
#        config = raffaello.parse_config_file('../examples/dmesg.cfg')
#        dmesg_ref = open('./dmesg-raffaello-short.log').read().splitlines() # to remove newlines
#        dmesg_log = [raffaello.paint(line, config) for line in open('dmesg-nocolor-short.log').read().splitlines()]
#
#        self.assertEqual(len(dmesg_log), len(dmesg_ref))
#
#        for log, ref in zip(dmesg_log, dmesg_ref):
#            self.assertEqual(log, ref)
#
#    def testPaintFromCommandLine(self):
#        # Dmesg test
#        os.system('cat dmesg-nocolor.log | raffaello --file=dmesg.cfg > /tmp/dmesg-cmd-test.log')
#
#        dmesg_log = open('/tmp/dmesg-cmd-test.log').readline()
#        dmesg_ref = open('./dmesg-raffaello.log').readline()
#
#        #self.assertEqual(len(dmesg_log), len(dmesg_ref))
#        self.assertEqual(dmesg_log, dmesg_ref)
#
#
#
#if __name__ == '__main__':
#    unittest.main()
#
