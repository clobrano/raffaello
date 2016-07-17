from raffaello import Palette, Terminal256Palette

p = Palette()
keys = p.keys()
keys.sort()

for color in keys:
    print('%s: %s' % (color, p[color].apply('test', 'test')))

p = Terminal256Palette()
keys = p.keys()
keys.sort()

for color in keys:
    print('%s: %s' % (color, p[color].apply('test', 'test')))


