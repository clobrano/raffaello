#!/usr/bin/env python
"""
Raffaello is a powerful, yet simple to use, output colorizer.

Usage: raffaello (-p PRESET | -r REQUEST | -f FILE | -l) [options]

    -p PRESET, --preset=PRESET              Prebuilt config files for coloring known output streams (gcc/g++, cmake, dmesg, gcc/g++, ModemManager, logcat...)
    -r REQUEST --request=REQUEST            The requested text/color mapping string. Multipe requests are separated by a space. Regular expression are supported. E.g. "error=>red [Ww]arning=>yellow_bold".
    -f FILE --file=FILE                     Path to the custom text=>color configuration file.
    -c COMMAND --command=COMMAND            Instead of using raffaello with pipes, set the command-line tool to be executed by raffaello directly. E.g. -c "dmesg -w".
    -m, --match-only                        Print only the lines that match against some defined pattern.
    -d DELIMITER --delimiter=DELIMITER      If you don't like "=>" as delimiter between text and color, use this flag to change it. E.g. -d & [default: =>]
    -l, --list                              List all the available colors and presets
    -v --verbose                            Enable debug logging
"""

import collections
import glob
import logging
import os
import re
import signal
import sys
from docopt import docopt

LEVEL = logging.INFO
logging.basicConfig(level=LEVEL, format='%(message)s')
LOG = logging.getLogger(__name__)

# Catch CTRL_C to let the program quit smoothly
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

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
        for item in self.commission:
            pattern = item.keys()[0]
            brush = item[pattern]
            try:
                matches = re.findall(pattern, line)
            except re.error as error:
                LOG.error('Error in line %s: %s', line, error)
                return None

            if matches:
                has_matches = True
                LOG.debug('Match found: %s => key:"%s", pattern:"%s"',
                          item, pattern, brush)
                LOG.debug(r'pre brush: %s', repr(copy))
                if brush.open is not None:
                    copy = brush.apply(copy, matches)
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
                    line = raw_input()
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


class Palette(collections.MutableMapping):
    '''
    Container of all available colors and styles.
    '''

    esc = chr(27)
    end = esc + '[0m'

    def __init__(self):
        collections.MutableMapping.__init__(self)
        self._palette = dict()
        self._set_colors()

    def _set_colors(self):
        esc = Palette.esc
        end = Palette.end

        fg_8color_offset = 30
        names = ['black', 'red', 'green', 'yellow', 'blue',
                 'magenta', 'cyan', 'light_gray']
        base_code = esc + '[%dm'

        color_codes = {names[num]: base_code % (num + fg_8color_offset)
                       for num in range(8)}
        style_bold = esc + '[1m'
        style_underline = esc + '[4m'

        for key, color_code in color_codes.items():
            brush = BrushStroke(key, color_code, end)
            self._palette.update({key: brush})

            # bold style
            brush = BrushStroke(key, color_code + style_bold, end)
            self._palette.update({key + '_bold': brush})

            # underline style
            brush = BrushStroke(key, color_code + style_underline, end)
            self._palette.update({key + '_underlined': brush})

        # blind code
        brush = BrushStroke('blind', None, None)
        self._palette.update({'blind': brush})

        return color_codes

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
    '''Color palette for Terminal with 256 colors'''
    def _set_colors(self):
        color_codes = Palette._set_colors(self)
        esc = Palette.esc
        end = Palette.end
        bg_color = 'bgcolor%03d'
        fg_color = 'color%03d'
        fg_code = esc + '[38;5;%dm'
        bg_code = esc + '[48;5;%dm'
        style_bold = esc + '[1m'
        style_underline = esc + '[4m'

        color_codes.update({bg_color % num: bg_code % num
                            for num in xrange(256)})
        color_codes.update({fg_color % num: fg_code % num
                            for num in xrange(256)})

        for key, color_code in color_codes.items():
            brush = BrushStroke(key, color_code, end)
            self._palette.update({key: brush})

            # bold style
            brush = BrushStroke(key, color_code + style_bold, end)
            self._palette.update({key + '_bold': brush})

            # underline style
            brush = BrushStroke(key, color_code + style_underline, end)
            self._palette.update({key + '_underlined': brush})


class Commission(object):
    '''
    The requested pattern-to-color mapping
    '''

    def __init__(self, request, delimiter='=>'):
        self.commission = []

        # Support multiline request
        requests = request.splitlines()
        if len(requests) == 1:
            # Check whether there are multiple requests in a single line
            requests = request.split(' ')

        for req in requests:
            # empty line
            if not req:
                continue

            if len(re.findall(delimiter, req)) > 1:
                print(re.findall(delimiter, req))
                LOG.error('[Error] Can not parse request %s. Too many '
                          'delimiters (%s) in request', req, delimiter)
                sys.exit(os.EX_DATAERR)

            try:
                pattern, color = req.split(delimiter)
            except ValueError as err:
                LOG.error("Could not parse request '%s'. %s)", req, err)
                LOG.debug("delimiter: %s", delimiter)
                sys.exit(os.EX_DATAERR)

            palette = Terminal256Palette()

            if color in palette:
                item = {r'%s' % pattern: palette[color]}
                LOG.debug('adding "%s"', item)
                self.commission.append(item)
            else:
                LOG.error('Color "%s" does not exist', color)
                sys.exit(os.EX_DATAERR)


class BrushStroke(object):
    """
    BrushStroke knows how to apply colors to the SHELL
    """

    def __init__(self, name, open_code, close_code):
        self.name = name
        self.open = open_code
        self.close = close_code

    def apply(self, line, matches):
        '''
        Apply brush to all matches in line
        '''
        for match in matches:
            if self.open is None:
                return None
            replacement = self.open + match + self.close
            line = line.replace(match, replacement)

        return line

    def __repr__(self):
        return self.name


class Configuration(object):
    '''Manages Raffaello's configuration'''

    def __init__(self, docopt_dict):
        config = docopt_dict
        root = os.path.abspath(os.path.dirname(__file__))
        self.presets = os.path.join(root, 'presets')
        self.custom_presets = HOME

        self.command = config['--command']
        self.match_only = config['--match-only']
        self.delimiter = config['--delimiter']

        if config['--list']:
            self._show_colors()
            self._show_styles()
            self._show_presets()
            sys.exit(os.EX_OK)

        elif config['--file']:
            path = config['--file']
            fullpath = self._get_full_path(path)

            if fullpath is None:
                LOG.error("Could not find configuration file %s", path)
                sys.exit(os.EX_CONFIG)

            self.request = self.read_commission_from_file(fullpath)

        elif config['--preset']:
            path = os.path.join(self.presets, config['--preset'])
            if os.path.exists(path):
                LOG.debug('Looking for preset "%s" in path %s"',
                          config['--preset'], path)
                self.request = self.read_commission_from_file(path)
            else:
                LOG.fatal('Could not find any preset with name \'%s\'',
                          config['--preset'])
                LOG.info('If you wanted to use a custom color file,'
                         ' you need the --file flag')
                sys.exit(os.EX_UNAVAILABLE)
        else:
            self.request = config['--request']

        if self.request:
            LOG.debug('Got request: \"%s\"', self.request)

    def _show_colors(self):
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
            palette['color001'].apply('color001', ['color001']),
            palette['bgcolor001'].apply('bgcolor001', ['bgcolor001']),
            palette['color001_bold'].apply('color001_bold', ['color001_bold']),
            palette['color001_underlined'].apply('color001_underlined', ['color001_underlined']),
        ))
        color_names = palette.keys()
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
                sys.stdout.write(' ' + color_num + ': ' + palette[color].apply(string, [string]))
                sys.stdout.flush()

                col -= 1
                if col == 0:
                    col = 10
                    print('')
        print('')

    def _show_styles(self):
        pass

    def _show_presets(self):
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

              List of the available presets
              -----------------------------
              ''')
        presets = glob.glob(os.path.join(self.presets, '*'))
        presets.sort()
        for preset in presets:
            name = os.path.basename(preset)
            if '__init__' in name:
                continue
            LOG.debug('Reading preset ' + preset)
            description = file(preset, mode='r').readlines()[0].strip()
            if description[0] == '#':
                print('%15s: %s', name, description.replace('#', '').lstrip())
            else:
                print('%15s:', name)

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


def main():
    '''Entry point'''
    # Parse command line arguments
    docopt_dict = docopt(__doc__)
    global LEVEL
    if docopt_dict['--verbose']:
        LEVEL = logging.DEBUG
    else:
        LEVEL = logging.DEBUG
    logging.basicConfig(level=LEVEL, format='    %(levelname)s,(message)s')

    global LOG
    LOG = logging.getLogger(__name__)

    config = Configuration(docopt_dict)
    commission = Commission(config.request, config.delimiter).commission
    raffaello = Raffaello(commission=commission, match_only=config.match_only)
    sys.exit(raffaello.start())


if __name__ == '__main__':
    main()
