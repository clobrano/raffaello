'''
Paint toolkit
'''
import collections


def brush_stroke(string, matches, brush):
    '''Apply color to matching words in string'''
    for match in matches:
        replacement = '%s%s%s' % (brush['open_color_tag'], match, brush['close_color_tag'])
        string = string.replace(match, replacement)

    return string


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
            # brush = Brush(key, color_code, end)
            brush = {'name': key,
                     'open_color_tag': color_code,
                     'close_color_tag': end}
            self._palette.update({key: brush})

            # bold style
            # brush = Brush(key, color_code + style_bold, end)
            brush = {'name': key,
                     'open_color_tag': color_code + style_bold,
                     'close_color_tag': end}
            self._palette.update({key + '_bold': brush})

            # underline style
            # brush = Brush(key, color_code + style_underline, end)
            brush = {'name': key,
                     'open_color_tag': color_code + style_underline,
                     'close_color_tag': end}
            self._palette.update({key + '_underlined': brush})

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
                            for num in range(256)})
        color_codes.update({fg_color % num: fg_code % num
                            for num in range(256)})

        for key, color_code in color_codes.items():
            # brush = BrushStroke(key, color_code, end)
            brush = {'name': key,
                     'open_color_tag': color_code,
                     'close_color_tag': end}
            self._palette.update({key: brush})

            # bold style
            # brush = BrushStroke(key, color_code + style_bold, end)
            brush = {'name': key,
                     'open_color_tag': color_code + style_bold,
                     'close_color_tag': end}
            self._palette.update({key + '_bold': brush})

            # underline style
            # brush = BrushStroke(key, color_code + style_underline, end)
            brush = {'name': key,
                     'open_color_tag': color_code + style_underline,
                     'close_color_tag': end}
            self._palette.update({key + '_underlined': brush})
