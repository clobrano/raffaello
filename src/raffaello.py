#!/usr/bin/env python
'''
Raffaello is a powerful, yet simple to use, output colorizer.

Usage: raffaello (-r REQUEST | -f FILE | -l) [options]

    -r REQUEST --request=REQUEST            The requested text/color mapping string. Multipe requests are separated by a space. Regular expression are supported. E.g. "error=>red [Ww]arning=>yellow_bold".
    -f FILE --file=FILE                     Path to the custom text=>color configuration file.
    -m, --match-only                        Print only the lines that match against some defined pattern.
    -d DELIMITER --delimiter=DELIMITER      If you don't like "=>" as delimiter between text and color, use this flag to change it. E.g. -d & [default: =>]
    -l, --list                              List all the available colors and presets
    -v --verbose                            Enable debug logging
'''

import os
import sys
import re
import signal
import logging
from docopt import docopt
from paint import Terminal256Palette, brush_stroke

logging.basicConfig(level=logging.INFO, format='%(message)s')
LOG = logging.getLogger(__name__)


class Raffaello(object):
    '''Highlight words according to given request'''

    def __init__(self, commission, match_only=False):
        self.commission = commission
        self.match_only = match_only

    def paint(self, line):
        '''
        Highlight patterns in line according to the given
        pattern-to-color dictionary
        '''
        copy = line.rstrip()
        has_changed = False
        for step in self.commission:
            pattern, brush = step

            try:
                matches = re.findall(pattern, line)

                if matches:
                    LOG.debug('matches of %s in: %s', pattern, line)
                    has_changed = True
                    copy = brush_stroke(copy, matches, brush)
            except re.error as error:
                LOG.error('Error in line %s: %s', line, error)
                continue

        if not has_changed and self.match_only:
            return None

        return copy

    def start(self):
        ''' Run raffaello as a command-line utility '''

        while True:
            try:
                line = self.paint(input())

                if line:
                    print(line)

            except KeyboardInterrupt:
                break

            except EOFError:
                LOG.debug("EOF reached. Nothing else to do")

                break

        LOG.debug("End of stream")
        sys.exit(os.EX_OK)


def get_color_file_path(filepath):
    '''Returns the full path of the color file'''

    root = os.path.abspath(os.path.dirname(__file__))
    home = os.path.expanduser(os.path.join('~', '.raffaello'))

    locations = [
        os.path.expanduser(filepath),
        os.path.join(root, 'presets', filepath),
        os.path.join(home, filepath)]

    for location in locations:
        if os.path.exists(location):
            return location

    LOG.fatal('could not find color file "%s"', filepath)

    return None


def read_request_from_file(path):
    ''' Get Pattern/Color pairs from configuration file '''

    LOG.debug('Reading config file %s', path)
    config = map(lambda x: x.strip(), open(path).readlines())
    request = list()

    for line in filter(lambda x: x and x[0] != '#', config):
        if line.startswith('include '):
            nested_config_file = line.split()[1]
            LOG.debug('including color file "%s"', nested_config_file)

            fullpath = get_color_file_path(nested_config_file)

            if not fullpath:
                LOG.error('could not find nested color file %s at %s',
                          nested_config_file, fullpath)

                continue

            request.extend(read_request_from_file(fullpath))

            continue

        request.append(line)

    return request


def parse_string_request(request, delimiter='=>'):
    '''Parse request string and return a list of pattern-to-color maps'''
    requests = request.splitlines()

    if len(requests) == 1:
        requests = request.split(' ')

    return parse_request(requests, delimiter)


def parse_request(requests, delimiter='=>'):
    '''Parse requests list and return a list of pattern-to-color maps'''
    commission = list()

    palette = Terminal256Palette()
    for req in filter(lambda x: x and len(x), requests):
        try:
            pattern, color = req.split(delimiter)
        except ValueError as err:
            if len(re.findall(delimiter, req)) > 1:
                LOG.error('could not parse request "%s": Too many delimiters (%s) in request', req, delimiter)
            else:
                LOG.error("could not parse request '%s'. %s", req, err)

            sys.exit(os.EX_DATAERR)

        if color not in palette:
            LOG.error('Color "%s" does not exist', color)
            sys.exit(os.EX_DATAERR)

        item = [r'%s' % pattern, palette[color]]
        LOG.debug('adding "%s"', item)
        commission.append(item)

    LOG.debug('commission is %s', commission)
    return commission


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

    color_names = list(palette.keys())
    color_names.sort()
    col = 10

    for color in filter(lambda x: '_' not in x, color_names):
        if color.startswith('bg'):
            color_num = re.match(r'bgcolor(\d+)', color).group(1)
            out = ' %s: %s' % (color_num, brush_stroke('   ', ['   '], palette[color]))
            sys.stdout.write(out)
            sys.stdout.flush()

            col -= 1

            if col == 0:
                col = 10
                print('')
    print('')


def show_presets():
    '''Preset help message'''
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

    request = conf['--request']
    color_file = conf['--file']

    if request:
        commission = parse_string_request(request, conf['--delimiter'])

    elif color_file:
        fullpath = get_color_file_path(color_file)

        if not fullpath:
            LOG.fatal('%s file not found', color_file)
            sys.exit(os.EX_CONFIG)

        request = read_request_from_file(fullpath)
        commission = parse_request(request, conf['--delimiter'])

    else:
        LOG.fatal('You are expected to give a color request')
        sys.exit(os.EX_CONFIG)

    raffaello = Raffaello(commission=commission, match_only=conf['--match-only'])
    sys.exit(raffaello.start())


if __name__ == '__main__':
    main()
