#!/usr/bin/env python
"""
Raffaello is a powerful yet simple to use command line (CLI) output colorizer.

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
level = logging.INFO
logging.basicConfig(level=level, format='    %(levelname)s %(message)s');
log = logging.getLogger(__name__)


# Default directory
root = '/'
home = os.path.join(root, 'home', 'carlo', '.raffaello')

piping = False

# Separator between Raffaello configuration and
# command to execute
command_separator = '---'

# Separator between pattern and color code
pattern_separator = '=>'

def usage():
    print(__doc__)

def help():
    usage()
    log.info('Available color list. NOTE that some colors could be unsupported on your terminal.\n')
    print(sorted(color_filters.keys()))

# [ COLOR CODES]
color_codes = {
    'black'            : chr(27)+'[30m',
    'red'            : chr(27)+'[31m',
    'green'            : chr(27)+'[32m',
    'brown'            : chr(27)+'[33m',
    'blue'            : chr(27)+'[34m',
    'purple'        : chr(27)+'[35m',
    'cyan'            : chr(27)+'[36m',
    'light_grey'    : chr(27)+'[37m',
    'dark_grey'        : chr(27)+'[30m',
    'light_red'        : chr(27)+'[31m',
    'light_green'    : chr(27)+'[32m',
    'yellow'        : chr(27)+'[33m',
    'light_blue'    : chr(27)+'[34m',
    'light_purple'    : chr(27)+'[35m',
    'light_cyan'    : chr(27)+'[36m',
    'white'            : chr(27)+'[37m'
}
end_color = chr(27)+'[39m'

# [ STYLE CODES ]
style_codes = {
    'bold' : chr(27) + '[1m',
}
end_bold = chr(27) + '[22m'


class Filter(object):
    """
    Encapsulate open and close tag codes
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


def get_options(optargs):
    """
    Parse command-line options
    """
    global piping
    global pattern_separator

    arguments_line = ' '.join(optargs)

    if '-h' in arguments_line or '--help' in arguments_line:
        help()
        sys.exit(0)

    if not command_separator in arguments_line:
        log.debug("No command separator found. Are we using pipes? Let's try")
        piping = True

    if not pattern_separator in arguments_line\
            and not 'file' in arguments_line:
        log.error("Ill-formatted raffaello's options")
        usage()
        sys.exit(1)

    options = arguments_line.split(command_separator)[0]

    if not piping:
        command = arguments_line.split(command_separator)[1]
    else:
        command = None

    pattern_sep_option = None
    if '--sep' in options or '-s' in options:
        pattern_sep_option = re.findall("-s=.", options)
        if not pattern_sep_option:
            pattern_sep_option = re.findall("--sep=.", options)

    if pattern_sep_option:
        pattern_separator = pattern_sep_option[0].split('=')[1]
        log.debug("Changed pattern_separator in %s" % pattern_separator)
        options = options.split(' ')[1:]
        log.debug('Remaining options: {0}'.format(options))

    patterns = {}

    if '--file' in options or '-f' in options:
        path = options.split('=')[1].rstrip()
        epath = os.path.expanduser(path)

        if not os.path.exists(epath):
            log.info("Looking for config file '%s' in '%s' folder..." % (epath, home))
            epath = os.path.join(home, os.path.basename(path))

            if os.path.exists(epath):
                log.info("Config file found")
            else:
                log.error('Could not find config file "%s"' % path)
                sys.exit(1)

        patterns = parse_config_file(epath)

    else:
        patterns = parse_color_option(options)

    return (patterns, command)



def parse_color_option(color_options):
    """
    A color option is a string in the form
    pattern=>color. No space is allowed at both sides
    of the double equal (=>) sign.
    """

    patterns = {}

    for option in color_options.split(' '):
        if len(option) == 0:
            continue

        if len(re.findall(pattern_separator, option)) > 1:
            log.error('[Error] Can not parse option %s. Too many pattern_separator symbols (%s) in option' % (option, pattern_separator))
            sys.exit(1)

        try:
            pattern, color = option.split(pattern_separator)
        except ValueError as err:
            log.error("Could not parse option '%s'. (%s)" % (option, err))
            log.debug("Color options: {0}".format(color_options))
            log.debug("pattern_separator: {0}".format(pattern_separator))
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



def parse_config_file(path):
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


def paint(line):
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


def run(command):

    if command:
        pipe_read, pipe_write = os.pipe()

        proc_id = os.fork()

    # child process executes the given command,
    #    parent process parses its output
    if command and proc_id:
        # run the provided command
        os.close(pipe_read)

        # redirect stdout to pipe
        os.dup2(pipe_write, sys.stdout.fileno())
        os.dup2(pipe_write, sys.stderr.fileno())

        os.system(command)

    else:
        if command:
            # read and modify command output
            os.close(pipe_write)
            fd_read = os.fdopen(pipe_read)

        while True:
            try:
                if not command:
                    line = raw_input()
                else:
                    line = fd_read.readline().rstrip()

                if line:
                    print(paint(line))
                else:
                    break
            except KeyboardInterrupt:
                pass
            except EOFError:
                log.debug("EOF reached. Nothing to do");
                break;
        os._exit(os.EX_OK)

    return 0


def main():
    global patterns
    global command
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    patterns, command = get_options(sys.argv[1:])
    sys.exit(run(command))



if __name__ == '__main__':
    print home
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    command = None
    patterns, command = get_options(sys.argv[1:])
    sys.exit(run(command))
