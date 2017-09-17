'''
Paint toolkit
'''
from collections import MutableMapping


def brush_stroke(string, matches, brush):
    '''Apply color to matching words in string'''

    for match in matches:
        replacement = '%s%s%s' % (brush['open_color_tag'], match, brush['close_color_tag'])
        string = string.replace(match, replacement)

    return string


class Palette(MutableMapping):
    '''
    Container of all available colors and styles.
    '''

    esc = chr(27)
    end = esc + '[0m'

    def __init__(self):
        MutableMapping.__init__(self)

        self._palette = dict()

        fg_7color_offset = 30
        names = ['black', 'red', 'green', 'yellow', 'blue',
                 'magenta', 'cyan', 'light_gray']

        base_code_template = Palette.esc + '[%dm'
        color_codes = {name: base_code_template % (i + fg_7color_offset)
                       for i, name in enumerate(names)}

        bold_style = Palette.esc + '[1m'
        underline_style = Palette.esc + '[4m'

        self._set_palette(
            color_codes,
            _bold=bold_style,
            _underlined=underline_style)

    def _set_palette(self, color_codes, **styles):
        for key, color_code in color_codes.items():
            brush = {'name': key,
                     'open_color_tag': color_code,
                     'close_color_tag': Palette.end}
            self._palette.update({key: brush})

            for style_name, style_code in styles.items():
                brush = {'name': key + style_name,
                         'open_color_tag': color_code + style_code,
                         'close_color_tag': Palette.end}
                self._palette.update({key + style_name: brush})

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
    '''Palette for 256 colors Terminals'''
    def __init__(self):
        Palette.__init__(self)

        fg_color_template = 'color%03d'
        fg_end_template = Palette.esc + '[38;5;%dm'

        color_codes = dict()
        color_codes.update({fg_color_template % num: fg_end_template % num
                            for num in range(256)})
        bold_style = Palette.esc + '[1m'
        underline_style = Palette.esc + '[4m'
        self._set_palette(
            color_codes, _bold=bold_style, _underlined=underline_style)

        bg_color_template = 'bgcolor%03d'
        bg_end_template = Palette.esc + '[48;5;%dm'

        color_codes = dict()
        color_codes.update({bg_color_template % num: bg_end_template % num
                            for num in range(256)})
        self._set_palette(color_codes)
