#!/usr/bin/env python
"""
Raffaello is a powerful, yet simple to use, output colorizer. You are now using

Usage: raffaello (-r REQUEST | -f FILE) [options]

-r REQUEST --request=REQUEST            The requested text/color mapping. E.g. "error=>red warning=>yellow_bold". Regex supported.
-f FILE --file=FILE                     Path to the text/color configuration file
-c COMMAND --command=COMMAND            The command-line tool to be executed. E.g. -c "dmesg -w".
-d DELIMITER --delimiter=DELIMITER      If you don't like "=>" as delimiter, use this flag to change it. [default: =>]
-t, --themes                            Prebuild themes for coloring known tools (dmesg, gcc/g++, ModemManager, logcat...)
-l, --list                              List available themes and colors
"""

import sys
import os
import re
import logging
import collections
import signal
from docopt import docopt

level = logging.INFO
logging.basicConfig(level=level, format='    %(levelname)s %(message)s')
log = logging.getLogger(__name__)

signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# Default directory
home = os.path.expanduser(os.path.join('~', '.raffaello'))


class Palette(collections.MutableMapping):
    '''
    Container of all available colors and styles.
    '''

    ESC = chr(27)
    END = ESC + '[0m'
    def __init__(self):
        self._palette = dict()
        self._generate()

    def _generate(self):
        foreground_color_offset = 30
        names = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'light_gray']
        base_code = Palette.ESC + '[%dm'
        color_codes = {names[num]: base_code % (num + foreground_color_offset) for num in range(8)}
        end_color = Palette.ESC +'[39m'
        style_bold = Palette.ESC + '[1m'
        end_bold = Palette.ESC + '[22m'

        for key, color_code in color_codes.items():
            brush = BrushStroke(key, color_code, end_color)
            self._palette.update({key: brush})

            # bold version
            brush = BrushStroke(key,
                                '%s%s' % (color_code, style_bold),
                                end_bold + end_color)
            self._palette.update({'%s_bold' % key: brush})

    def __getitem__(self, key=''):
        return self._palette[key.lower()]

    def __iter__(self):
        return iter(self._palette)

    def __len__(self):
        return len(self._palette)

    def __delitem__(self, key):
        pass

    def __setitem__(self, key, item):
        pass


class Terminal256Palette(Palette):
    def _generate(self):
        bg_color = 'color%03d'
        fg_color = 'fgcolor%03d'
        end_color = chr(27)+'[0m'
        bg_code = Palette.ESC + '[38;5;%dm'
        fg_code = Palette.ESC + '[48;5;%dm'

        color_codes = {bg_color % num: bg_code % num for num in xrange(256)}
        color_codes.update({fg_color % num: fg_code % num for num in xrange(256)})

        for key, color_code in color_codes.items():
            brush = BrushStroke(key, color_code, Palette.END)
            self._palette.update({key: brush})


class Commission(object):
    '''
    The requested pattern to color mapping
    '''

    def __init__(self, request, delimiter='=>'):
        self.commission = []
        for r in request.split(' '):
            if len(r) == 0:
                continue

            if len(re.findall(delimiter, r)) > 1:
                log.error('[Error] Can not parse request %s.')
                log.error('    Too many pattern separator symbols (%s) in request'
                          % (r, delimiter))
                sys.exit(1)

            try:
                pattern, color = r.split(delimiter)
            except ValueError as err:
                log.error("Could not parse request '%s'. (%s)" % (r, err))
                log.debug("Color requests: {0}".format(rs))
                log.debug("delimiter: {0}".format(delimiter))
                sys.exit(1)

            # Remove initial quote if any
            matches = re.findall("^'", pattern)
            if matches:
                pattern = pattern[1:]

            # Remove final quote if any
            matches = re.findall("'$", pattern)
            if matches:
                pattern = pattern[:len(pattern) - 1]

            palette = Terminal256Palette()

            if color in palette:
                item = {r'%s' % pattern: palette[color]}
                log.debug('adding "{0}"'.format(item))
                self.commission.append(item)
            else:
                log.error('Color "%s" does not exist' % color)
                sys.exit(1)

        log.info('Commission is')
        log.info(self.commission)


class Raffaello (object):
    '''
    Wrapper class for methods that Raffaello
    uses when running as command-line utility
    '''

    def __init__(self, commission):
        '''Parse command line options'''

        config = docopt(__doc__)

        self.command = config['--command']
        self.commission = commission

        #if config['--file'] is None:
        #    # Inline 'pattern=>color' option list
        #    self.patterns = Commission(config['--request'], config['--delimiter']).commission
        #else:
        #    path = config['--file']
        #    fullpath = get_config_full_path(path)

        #    if fullpath is None:
        #        log.error("Could not find configuration file %s", path)
        #        sys.exit(1)

        #    self.patterns = parse_config_file(fullpath, config['--delimiter'])

    def paint(self, line, patterns):
        """
        Highlight line according to the given
        pattern/color dictionary
        """
        log.debug('paint line "%s"' % line)
        for item in patterns:
            pattern = item.keys()[0]
            brush = item[pattern]
            log.debug('considering {0} => key:"{1}", pattern:"{2}"'
                      .format(item, pattern, brush))
            try:
                matches = re.findall(pattern, line)
            except Exception as err:
                log.error('%s' % err)
                log.debug('line: %s' % line)
                sys.exit(1)

            if matches:
                log.debug('Match found')
                line = brush.apply(line, matches)

        return line.rstrip()

    def start(self):
        '''
        Run raffaello as a command-line utility
        '''
        command = self.command
        patterns = self.commission

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
                        log.debug('Is the end of the stream?')
                        if endofstream:
                            break
                        else:
                            endofstream = True
                    else:
                        endofstream = False

                    # And here is the magic
                    print(self.paint(line, patterns))

                except KeyboardInterrupt:
                    log.info("Bye!")
                    break

                except EOFError:
                    log.info("EOF reached. Nothing to do")
                    break

            log.debug("End of stream")
            os._exit(os.EX_OK)

        return 0


class BrushStroke(object):
    """
    BrushStroke knows how to apply colors to the SHELL
    """

    def __init__(self, name, open_code, close_code):
        self.__name = name
        self.open = open_code
        self.close = close_code

    def apply(self, line, matches):
        '''
        Apply brush to all matches in line
        '''
        for match in matches:
            replacement = '%s%s%s' % (self.open, match, self.close)
            line = line.replace(match, replacement)

        return line

    def __repr__(self):
        return self.__name


class Configuration(object):

    def __init__(self):
        config = docopt(__doc__, version=__version__)

        self.command = config['--command']

        if config['--file']:
            path = config['--file']
            fullpath = self._get_full_path(path)

            if fullpath is None:
                log.error("Could not find configuration file %s", path)
                sys.exit(1)

            self.request = self.read_commission_from_file(fullpath, config['--delimiter'])
        else:
            self.request = config['--request']

        log.info('Got request: \"%s\"' % self.request)

    def _get_full_path(self, filepath):
        '''Build the fullpath to config file'''
        log.debug('Building full path for "%s"' % filepath)
        fullpath = os.path.expanduser(filepath)

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


    def read_commission_from_file(self, path, delimiter='=>'):
        """
        Get Pattern/Color pairs from configuration file
        """
        log.debug('Reading config file %s' % path)
        config = open(path).readlines()
        request = ''
        patterns = []
        include_pattern = re.compile('^include (.*)')
        for line in config:
            line = line.rstrip()

            # Skip empty lines
            if 0 == len(line):
                continue

            # Skip comments
            if '#' == line[0]:
                continue

            # Check inner config files
            includes = include_pattern.match(line)
            if includes:
                subconfig = includes.group(1)
                log.debug('got subconfig %s' % subconfig)

                subconf_fullpath = self._get_full_path(subconfig)

                if subconf_fullpath:
                    inner_request = self.read_commission_from_file(subconf_fullpath, delimiter)
                    request.join(' ' + inner_request)
                    #patterns.extend(inner_request)
                    continue

            #new_pattern = Commission(line).commission
            #patterns.extend(new_pattern)
            request = request + '%s ' % line

        return request


def main():
    config = Configuration()
    commission = Commission(config.request).commission
    raffaello = Raffaello(commission)
    sys.exit(raffaello.start())


if __name__ == '__main__':
    '''
    This will permit to use raffaello without installing it
    into the filesystem (which is the suggested usage, though).
    '''
    main()
