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
    print('%s: %s' % (color, p[color].apply('This is a test string', ['test'])))


from raffaello import Raffaello, Commission

request = '''
error=>red
warning=>yellow_bold
bluish\stext=>color026
'''

c = Commission(request)
r = Raffaello(c.commission)

print(r.paint('Sample message with error, warning and a bluish text.'))
