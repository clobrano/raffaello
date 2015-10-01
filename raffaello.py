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
"""

import sys
import os
import re
import logging
import collections

__version__='2.2.0'
level = logging.INFO
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
    uses when running as command-line utility
    '''

    # Separator between Raffaello's options and CLI tool command
    cli_dlms = '---'
    # Separator between pattern and desired color
    pattern_dlms = '=>'
    command = None
    patterns = {}
    use_pipe = False


    def __check_cmd_line_format (self, cmd_line):
        if ('-h' in cmd_line) or ('--help' in cmd_line):
            self.help()
            sys.exit(0)

        if ('--version' in cmd_line) or ('-v' in cmd_line):
            print (__version__)
            sys.exit (0)

        if not self.cli_dlms in cmd_line:
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

        (options, self.command) = self.__get_cli_options (args)

        #options = self.__update_pattern_dlms (options)

        if ('--file' in options) or ('-f' in options):
            path = options.split ('=') [1].rstrip ()

            fullpath = get_config_full_path (path)

            if None == fullpath:
                log.error("Could not find configuration file %s", path);
                sys.exit(1)

            self.patterns = parse_config_file(fullpath, self.pattern_dlms)

        else:
            # Inline 'pattern=>color' option list
            self.patterns = parse_color_option(options, self.pattern_dlms)


    def __get_cli_options (self, args = []):
        '''
        Parses command line options and returns a tuple made of two elements:
        1. Raffaello's options.
        2. CLI tool whose output is to be colorized if provided, None otherwise.
        '''
        cmd_line = ' '.join (args)
        self.__check_cmd_line_format (cmd_line)

        opts_and_cmd = cmd_line.split (self.cli_dlms)
        options = opts_and_cmd [0]

        if 1 == len (opts_and_cmd):
            command = None
        else:
            command = opts_and_cmd [1]

        return (options, command)



    def usage (self):
        '''
        Print doc information
        '''
        print (__doc__)


    def help (self):
        self.usage ()
        log.info('Available color list.')
        print(sorted(color_filters.keys()))
        log.info('NOTE that some colors could be unsupported on your terminal.')


    def run (self):
        '''
        Run raffaello as a command-line utility
        '''
        command = self.command
        patterns = self.patterns

        # Raffaello encapsulates the command line command whose ouput
        #  is to be colorized
        if command:
            # Get output file's descriptors
            pipe_read, pipe_write = os.pipe()
            proc_id = os.fork()

        # Child process executes the given command,
        #  parent process (Raffaello) parses its output
        if command and proc_id:
            # Child
            os.close(pipe_read)

            # redirect stdout to pipe in order to let
            #  parent process read
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

            endofstream = False

            while True:
                try:
                    if not command:
                        # we are in a pipe, just read from output
                        line = raw_input()
                    else:
                        # we are not in a pipe, run from file's descriptors
                        line = fd_read.readline().rstrip()

                    if command and not line:
                        # Not using pipe, we need to understand when the
                        # program ends. Two empty lines will be considered
                        # as the end of the stream
                        log.debug ('Is the end of the stream?')
                        if endofstream:
                            break
                        else:
                            endofstream = True
                    else:
                        endofstream = False

                    # And here is the magic
                    print(paint(line, patterns))

                except KeyboardInterrupt:
                    log.info("User iterruption")
                    pass

                except EOFError:
                    log.info("EOF reached. Nothing to do");
                    break;

            log.debug("End of stream")
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


# ======================================================
# Utilities
# ======================================================
def get_config_full_path (filepath):
    '''Build the fullpath to config file'''
    log.debug ('Building full path for "%s"' % filepath)
    fullpath = os.path.expanduser (filepath)

    if not os.path.exists(fullpath):
        log.debug("Looking for config file '%s' in '%s' folder..." %
                (filepath, home))
        fullpath = os.path.join(home, os.path.basename(fullpath))

        if os.path.exists(fullpath):
            log.debug("Using '%s'" % fullpath)
        else:
            log.error('Could not find config file "%s"' % filepath)
            fullpath = None

    return fullpath




def parse_color_option(color_options, pattern_dlms='=>'):
    """
    A color option is a string in the form
    pattern=>color. No space is allowed at both sides
    of the double equal (=>) sign.
    """

    patterns = []

    for option in color_options.split(' '):
        if len(option) == 0:
            continue

        if len(re.findall(pattern_dlms, option)) > 1:
            log.error('[Error] Can not parse option %s.')
            log.error('    Too many pattern separator symbols (%s) in option'\
                    % (option, pattern_dlms))
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
            item = {r'%s' % pattern : color_filters[color]}
            log.debug ('adding "{0}"'.format (item))
            patterns.append (item)
        else:
            log.error('Color "%s" does not exist' % color)
            sys.exit(1)

    log.debug ('returnining {0}'.format (patterns))
    return patterns



def parse_config_file(path, pattern_dlms='=>'):
    """
    Get Pattern/Color pairs from configuration file
    """
    log.debug('Reading config file %s' % path)
    config = open(path).readlines()
    patterns = []
    include_pattern = re.compile ('^include (.*)')
    for line in config:
        line = line.rstrip()

        # Skip empty lines
        if 0 == len (line):
            continue

        # Skip comments
        if '#'== line [0]:
            continue

        # Check inner config files
        includes = include_pattern.match (line)
        if includes:
            subconfig = includes.group (1)
            log.debug ('got subconfig %s' % subconfig)

            subconf_fullpath = get_config_full_path (subconfig)

            if subconf_fullpath:
                subdict = parse_config_file (subconf_fullpath, pattern_dlms)
                patterns.extend (subdict)
                continue

        new_pattern = parse_color_option(line)

        patterns.extend (new_pattern)

    return patterns


def paint(line, patterns):
    """
    Highlight line according to the given
    pattern/color dictionary
    """
    log.debug ('paint line "%s"' % line)
    for item in patterns:
        pattern = item.keys () [0]
        filter = item [pattern]
        log.debug('considering {0} => key:"{1}", pattern:"{2}"'\
                .format (item, pattern, filter))
        try:
            matches = re.findall(pattern, line)
        except Exception as err:
            log.error('%s' % err)
            log.debug('line: %s' % line)
            sys.exit(1)

        if matches:
            log.debug('Match found')
            line = filter.apply(line, matches)

    return line.rstrip()



def main ():
    script = Script (sys.argv [1:])
    sys.exit (script.run ())


if __name__ == '__main__':
    '''
    This will permit to use raffaello without installing it
    into the filesystem (which is the suggested usage, though).
    '''
    main ()
