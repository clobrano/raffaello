#!/usr/bin/env python

"""
Raffaello is a powerful, yet simple to use, output colorizer. You are now using the script version.


Usage:

    raffaello <arguments> --- command-line-tool [command-line-tool-arguments]

    OR using pipe

    command-line-tool [command-line-tool-arguments] | raffaello <arguments>

    Pattern and color configuration is provided using "inline" patterns or --file parameter:

        $ raffaello "pattern1=>colorA" "pattern2=>colorB" "pattern3=>colorA" ... --- command [arguments]
        $ raffaello --file=/path/to/config/file --- command [arguments]

        e.g.

        $ raffaello '.*[Ee]rror.*=>red' --- dmesg    # this will highlight lines with error messages (if any) in red
        $ raffaello --file=dmesg.cfg --- dmesg

        $ cat dmesg.cfg
            # Dmesg config file example. Comment lines will be ignored
            .*[Ee]rror.*=>red_bold
            .*ERROR.*=>red_bold
            timed\sout=>red
            .*[Ww]arning.*=>yellow

Notes:

    1. no spaces are allowed at both sides of => sign
        error => red        WRONG
        error=> red        WRONG
        error =>red        WRONG
        error=>red        OK

    2. if a pattern contains spaces, they must be defined using "\s" symbol, for example:
        could not=>red_bold    WRONG
        could\snot=>red_bold    OK

    3. Raffaello looks for config files also in <HOME>/.raffaello hidden directory, so that

        $ raffaello --file=<home>/.raffaello/config-file...     is equal to
        $ raffaello --file=config-file
"""

import sys
import os
import re
import logging


__version__='2.0.0'
level = logging.DEBUG
logging.basicConfig(level=level, format='    %(levelname)s %(message)s');
log = logging.getLogger(__name__)


# Default directory
home = os.path.expanduser (os.path.join('~', '.raffaello'))

# [ COLOR CODES]
color_codes = {
    'black'        : chr(27)+'[30m',
    'red'          : chr(27)+'[31m',
    'green'        : chr(27)+'[32m',
    'brown'        : chr(27)+'[33m',
    'blue'         : chr(27)+'[34m',
    'purple'       : chr(27)+'[35m',
    'cyan'         : chr(27)+'[36m',
    'light_grey'   : chr(27)+'[37m',
    'dark_grey'    : chr(27)+'[30m',
    'light_red'    : chr(27)+'[31m',
    'light_green'  : chr(27)+'[32m',
    'yellow'       : chr(27)+'[33m',
    'light_blue'   : chr(27)+'[34m',
    'light_purple' : chr(27)+'[35m',
    'light_cyan'   : chr(27)+'[36m',
    'white'        : chr(27)+'[37m'
}
end_color = chr(27)+'[39m'

# style codes
style_codes = {
    'bold' : chr(27) + '[1m',
}
end_bold = chr(27) + '[22m'


class Script (object):
    '''
    Wrapper class for methods that Raffaello
    uses when run as command-line utility
    '''

    cmd_dlms = '---'
    pattern_dlms = '=>'
    command = None
    patterns = {}
    use_pipe = False

    def __check_cmd_line_format (self, cmd_line):
        if ('-h' in cmd_line) or ('--help' in cmd_line):
            help()
            sys.exit(0)

        if not self.cmd_dlms in cmd_line:
            log.debug("No command separator found. Are we using pipes?")
            self.use_pipe = True

        if (not self.pattern_dlms in cmd_line) and\
                (not 'file' in cmd_line):
                    log.debug ('pattern_dlms: {0}'.format (self.pattern_dlms))
                    log.error("Ill-formatted raffaello's options")
                    self.usage()
                    sys.exit(1)


    def __update_pattern_dlms (self, options):
        '''Manage custom pattern_dlms'''
        custom_dlms = None
        if ('--sep' in options) or ('-s' in options):
            custom_dlms = re.findall ('-s=.', options)
            if not custom_dlms:
                custom_dlms = re.findall ('--sep=.', options)

        if custom_dlms:
            self.pattern_dlms = custom_dlms [0].split ('=') [1]
            log.debug ('Changed pattern delimiters in "%s"' % self.pattern_dlms)
            options = options.split (' ') [1:]
            log.debug ('Remaining options: {0}'.format (options))

        return options


    def __init__ (self, args = []):
        '''Parse command line options'''

        if 2 > len (args):
            self.usage ()
            sys.exit (1)

        cmd_line = ' '.join (args)
        self.__check_cmd_line_format (cmd_line)

        opt_and_cmd = cmd_line.split (self.cmd_dlms)

        options = opt_and_cmd [0]

        if 1 == len (opt_and_cmd):
            self.command = None
        else:
            self.command = opt_and_cmd [1]

        #options = self.__update_pattern_dlms (options)

        if ('--file' in options) or ('-f' in options):
            path = options.split ('=') [1].rstrip ()
            epath = os.path.expanduser(path)

            # Let use relative path
            if not os.path.exists(epath):
                log.info("Looking for config file '%s' in '%s' folder..." % (epath, home))
                epath = os.path.join(home, os.path.basename(path))

                if os.path.exists(epath):
                    log.info("Config file found")
                else:
                    log.error('Could not find config file "%s"' % path)
                    sys.exit(1)

                self.patterns = parse_config_file(epath, self.pattern_dlms)

        else:
            # Inline pattern=>color option list
            self.patterns = parse_color_option(options, self.pattern_dlms)


    def usage (self):
        '''
        Print doc information
        '''
        print (__doc__)


    def help (self):
        self.__usage ()
        log.info('Available color list. NOTE that some colors could be unsupported on your terminal.\n')
        print(sorted(color_filters.keys()))


    def run (self):
        '''
        Run raffaello as a script
        '''
        command = self.command
        patterns = self.patterns

        # Raffaello is encapsulating the command line command to colorize
        if command:
            # Get output file's descriptors
            pipe_read, pipe_write = os.pipe()
            proc_id = os.fork()

        # Child process executes the given command,
        #    parent process (Raffaello) parses its output
        if command and proc_id:
            # Child
            os.close(pipe_read)

            # redirect stdout to pipe in order to let
            # parent process read
            os.dup2(pipe_write, sys.stdout.fileno())
            os.dup2(pipe_write, sys.stderr.fileno())

            # execute the command
            os.system(command)

        else:
            # Parent
            if command:
                # read child's output
                os.close(pipe_write)
                fd_read = os.fdopen(pipe_read)

            # Process the output. This code is shared between when
            # raffaello is run as parent process and when is run throught pipe
            while True:
                try:
                    if not command:
                        # we are in a pipe, just read from ouptut
                        line = raw_input()
                    else:
                        # we are not in a pipe, run from file's descriptors
                        line = fd_read.readline().rstrip()

                    if line:
                        # And here is the magic
                        print(paint(line, patterns))

                    else:
                        break

                except KeyboardInterrupt:
                    pass

                except EOFError:
                    log.debug("EOF reached. Nothing to do");
                    break;

            os._exit(os.EX_OK)

        return 0




class Filter(object):
    """
    Encapsulate open and close tag codes for each color
    """
    def __init__(self, name, open_code, close_code):
        self.__name = name
        self.open = open_code
        self.close = close_code

    def apply(self, line, matches):
        '''
        Apply filter to all matches in line
        '''
        for match in matches:
            replacement = '%s%s%s' % (self.open, match, self.close)
            line = line.replace(match, replacement)

        return line


    def __repr__(self):
        return self.__name


# [ FILTERS ]
color_filters = {}
for key, color_code in color_codes.items():
    color_filter = Filter(key, color_code, end_color)
    color_filters.update({key : color_filter})

    # bold version
    color_filter = Filter(key, '%s%s' % (color_code, style_codes['bold']),
                            end_bold + end_color)
    color_filters.update({'%s_bold' % key : color_filter})



def parse_color_option(color_options, pattern_dlms='=>'):
    """
    A color option is a string in the form
    pattern=>color. No space is allowed at both sides
    of the double equal (=>) sign.
    """
    patterns = {}

    for option in color_options.split(' '):
        if len(option) == 0:
            continue

        if len(re.findall(pattern_dlms, option)) > 1:
            log.error('[Error] Can not parse option %s. Too many pattern separator symbols (%s) in option' % (option, pattern_dlms))
            sys.exit(1)

        try:
            pattern, color = option.split(pattern_dlms)
        except ValueError as err:
            log.error("Could not parse option '%s'. (%s)" % (option, err))
            log.debug("Color options: {0}".format(color_options))
            log.debug("pattern_dlms: {0}".format(pattern_dlms))
            sys.exit(1)

        # Remove initial quote if any
        matches = re.findall("^'", pattern)
        if matches:
            pattern = pattern[1:]

        # Remove final quote if any
        matches = re.findall("'$", pattern)
        if matches:
            pattern = pattern[:len(pattern) - 1]

        if color in color_filters:
            patterns.update( {r'%s' % pattern : color_filters[color]} )
        else:
            log.error('Color "%s" does not exist' % color)
            sys.exit(1)

    return patterns



def parse_config_file(path, pattern_dlms='=>'):
    """
    Get Pattern/Color pairs from configuration file
    """
    log.debug('Reading config file %s' % path)
    config = open(path).readlines()
    patterns = {}
    for line in config:
        line = line.rstrip()

        if len(line) == 0 or line[0] == '#':    # skip empty lines and comments
            continue

        new_pattern = parse_color_option(line)

        patterns.update(new_pattern)

    return patterns


def paint(line, patterns):
    """
    Highlight line according to the given
    pattern/color dictionary
    """
    for pattern, filter in patterns.items():
        try:
            matches = re.findall(pattern, line)
        except Exception as err:
            log.error('%s' % err)
            log.debug('pattern: %s' % pattern)
            log.debug('line: %s' % line)
            sys.exit(1)

        line = filter.apply(line, matches)
    return line.rstrip()



def main ():
    script = Script (sys.argv [1:])
    sys.exit (script.run ())
