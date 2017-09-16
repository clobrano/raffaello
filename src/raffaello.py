#!/usr/bin/env python
'''
Raffaello is a powerful, yet simple to use, output colorizer.

Usage: raffaello (-r REQUEST | -f FILE | -l) [options]

    -r REQUEST --request=REQUEST            The requested text/color mapping string. Multipe requests are separated by a space. Regular expression are supported. E.g. "error=>red [Ww]arning=>yellow_bold".
    -f FILE --file=FILE                     Path to the custom text=>color configuration file.
    -c COMMAND --command=COMMAND            Instead of using raffaello with pipes, set the command-line tool to be executed by raffaello directly. E.g. -c "dmesg -w".
    -m, --match-only                        Print only the lines that match against some defined pattern.
    -d DELIMITER --delimiter=DELIMITER      If you don't like "=>" as delimiter between text and color, use this flag to change it. E.g. -d & [default: =>]
    -l, --list                              List all the available colors and presets
    -v --verbose                            Enable debug logging
'''

import logging
import os
import re
import signal
import sys
from docopt import docopt
from paint import Terminal256Palette, brush_stroke

LEVEL = logging.INFO
logging.basicConfig(level=LEVEL, format='%(message)s')
LOG = logging.getLogger(__name__)

# Default directory
HOME = os.path.expanduser(os.path.join('~', '.raffaello'))


class Raffaello(object):
    '''
    Wrapper class for methods that Raffaello
    uses when running as command-line utility
    '''

    def __init__(self, commission, command=None, match_only=False):
        self.command = command
        self.commission = commission
        self.match_only = match_only

    def paint(self, line):
        """
        Highlight line according to the given
        pattern/color dictionary
        """
        copy = line
        has_matches = False
        for step in self.commission:
            pattern, brush = step

            try:
                matches = re.findall(pattern, line)
            except re.error as error:
                LOG.error('Error in line %s: %s', line, error)
                return None

            if matches:
                has_matches = True
                LOG.debug('Match found: %s => key:"%s", pattern:"%s"',
                          step, pattern, brush)
                LOG.debug(r'pre brush: %s', repr(copy))
                if brush['open_color_tag'] is not None:
                    copy = brush_stroke(copy, matches, brush)
                    copy = copy.rstrip()
                else:
                    return None
        if self.match_only and not has_matches:
            LOG.debug('Skipping %s because there is no match', copy)
            return None

        return copy

    def start(self):
        '''
        Run raffaello as a command-line utility
        '''
        command = self.command
        pipe_read = None
        pipe_write = None

        # Raffaello encapsulates the command line command whose ouput
        #  is to be colorized
        if command:
            # Get output file's descriptors
            pipe_read, pipe_write = os.pipe()
            proc_id = os.fork()

        # Child process executes the given command,
        #  parent process (Raffaello) parses its output
        if command and proc_id:
            self._manage_child(pipe_read, pipe_write)
        else:
            # Parent
            self._manage_parent(pipe_read, pipe_write)

        return 0

    def _manage_parent(self, pipe_read, pipe_write):
        command = self.command
        if command:
            # read child's output
            os.close(pipe_write)
            fd_read = os.fdopen(pipe_read)

            endofstream = False

        while True:
            try:
                if not command:
                    # we are in a pipe, just read from output
                    line = input()
                else:
                    # we are not in a pipe, read from file's descriptors
                    line = fd_read.readline().rstrip()

                    if not line:
                        # Not using pipe, we need to understand when the
                        # program ends. Two empty lines will be considered
                        # as the end of the stream
                        if endofstream:
                            break
                        else:
                            endofstream = True
                    else:
                        endofstream = False

                # And here is the magic
                line = self.paint(line)
                if line:
                    print(line)

            except KeyboardInterrupt:
                break

            except EOFError:
                LOG.debug("EOF reached. Nothing else to do")
                break

        LOG.debug("End of stream")
        sys.exit(os.EX_OK)

    def _manage_child(self, pipe_read, pipe_write):
        os.close(pipe_read)

        # redirect stdout to pipe in order to let
        #  parent process read
        os.dup2(pipe_write, sys.stdout.fileno())
        os.dup2(pipe_write, sys.stderr.fileno())

        # execute the command
        os.system(self.command)


def parse_request(request, delimiter='=>'):
    '''Parse request string and return a list of pattern-to-color maps'''
    commission = []
    # Support multiline request
    requests = request.splitlines()
    if len(requests) == 1:
        # Check whether there are multiple requests in a single line
        requests = request.split(' ')

    for req in requests:
        # empty line
        if not req:
            continue

        try:
            pattern, color = req.split(delimiter)
        except ValueError as err:
            if len(re.findall(delimiter, req)) > 1:
                LOG.error('could not parse request "%s": Too many '
                          'delimiters symbols (%s) in request', req, delimiter)
            else:
                LOG.error("could not parse request '%s'. %s)", req, err)

            sys.exit(os.EX_DATAERR)

        palette = Terminal256Palette()

        if color in palette:
            item = [r'%s' % pattern, palette[color]]
            LOG.debug('adding "%s"', item)
            commission.append(item)
        else:
            LOG.error('Color "%s" does not exist', color)
            sys.exit(os.EX_DATAERR)

    return commission


class Configuration(object):
    '''Manages Raffaello's configuration'''

    def __init__(self,
                 request=None,
                 command=None,
                 color_file=None,
                 match_only=False,
                 delimiter='=>'):
        root = os.path.abspath(os.path.dirname(__file__))
        self.presets = os.path.join(root, 'presets')
        self.custom_presets = HOME

        self.command = command
        self.match_only = match_only
        self.delimiter = delimiter

        if request:
            self.request = request
        elif color_file:
            fullpath = self._get_full_path(color_file)

            if not fullpath:
                LOG.error("Could not find configuration file %s", color_file)
                sys.exit(os.EX_CONFIG)

            self.request = self.read_commission_from_file(fullpath)
        else:
            LOG.error('no request found')

    def _get_full_path(self, filepath):
        '''Build the fullpath to config file'''
        LOG.debug('Building full path for "%s"...', filepath)
        fullpath = os.path.expanduser(filepath)

        if not os.path.exists(fullpath):
            # Is it a relative paths? Check in presets root
            fullpath = os.path.join(self.presets, os.path.basename(fullpath))

            if os.path.exists(fullpath):
                LOG.debug("Using '%s'", fullpath)
                return fullpath

            # Check in custom presets folder
            fullpath = os.path.join(self.custom_presets, HOME, os.path.basename(fullpath))

            if os.path.exists(fullpath):
                LOG.debug("Using '%s'", fullpath)
                return fullpath

            LOG.error('Could not find config file "%s"', filepath)
            fullpath = None

        return fullpath

    def read_commission_from_file(self, path):
        """
        Get Pattern/Color pairs from configuration file
        """
        LOG.debug('Reading config file %s', path)
        config = open(path).readlines()
        request = ''
        include_pattern = re.compile(r'^include (.*)')
        for line in config:
            line = line.rstrip()

            # Skip empty lines and commends
            if not line or line[0] == '#':
                continue

            # Check inner config files
            includes = include_pattern.match(line)
            if includes:
                subconfig = includes.group(1)
                LOG.debug('including preset "%s"', subconfig)

                subconf_fullpath = self._get_full_path(subconfig)

                if subconf_fullpath:
                    inner_request = self.read_commission_from_file(subconf_fullpath)
                    LOG.debug('included request "%s"', inner_request)
                    request = request + ' ' + inner_request
                    continue

            request = request + line + ' '

        return request


def show_colors():
    '''Show available colors and usage'''
    palette = Terminal256Palette()
    print('''
    8 bit color palette
    -------------------

        * Foreground color names are in the form 'colorNUM'. E.g. foreground red is %s
        * Background color names are in the form 'bgcolorNUM'. E.g. background red is %s

    For terminals that support 8 colors only, you can still use the following names:
        black, red, green, yellow, blue, magenta, cyan, light_gray

    Colors might have 2 styles (when supported by the terminal) and the name
    is in the form 'colorNUM_<style>':
        * Bold style: foreground red bold is %s
        * Underlined style: foreground red underlined is %s

    Following the full list of color NUMs
    ''' % (
        brush_stroke('color001', ['color001'], palette['color001']),
        brush_stroke('bgcolor001', ['bgcolor001'], palette['bgcolor001']),
        brush_stroke('color001_bold', ['color001_bold'], palette['color001_bold']),
        brush_stroke('color001_underlined', ['color001_underlined'], palette['color001_underlined'])
    ))
    # palette['color001'].apply('color001', ['color001']),
    # palette['bgcolor001'].apply('bgcolor001', ['bgcolor001']),
    # palette['color001_bold'].apply('color001_bold', ['color001_bold']),
    # palette['color001_underlined'].apply('color001_underlined', ['color001_underlined']),
    # ))

    color_names = list(palette.keys())
    color_names.sort()
    col = 10
    for color in color_names:
        # skip styled colors
        if '_' in color:
            continue

        # Foreground color is easy to see
        if color.startswith('bg'):
            color_num = re.match(r'bgcolor(\d+)', color).group(1)
            string = '   '
            sys.stdout.write(' ' + color_num + ': ' + brush_stroke(string, [string], palette[color]))
            sys.stdout.flush()

            col -= 1
            if col == 0:
                col = 10
                print('')
    print('')

def show_presets():
    print('''
          Presets
          -------

          A preset is a file containing a list of text=>color pairs for
          a specific output stream.
          Custom presets can be used using the --file directive providing
          the full path to the file or ony the relative path of it if it is
          stored in $HOME/.raffaello folder.
          Custom presets can reuse the built-in presets using the "include"
          directive
          E.g.

            include errors
            include custom-preset
            ...
          ''')


def main():
    '''Entry point'''

    # Catch CTRL_C to let the program quit smoothly
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    # Parse command line arguments
    conf = docopt(__doc__)

    if conf['--list']:
        show_colors()
        show_presets()
        return

    if conf['--verbose']:
        LOG.setLevel(logging.DEBUG)

    config = Configuration(
        request=conf['--request'],
        command=conf['--command'],
        color_file=conf['--file'],
        match_only=conf['--match-only'],
        delimiter=conf['--delimiter'])

    commission = parse_request(config.request, config.delimiter)
    raffaello = Raffaello(commission=commission, match_only=config.match_only)
    sys.exit(raffaello.start())


if __name__ == '__main__':
    main()
