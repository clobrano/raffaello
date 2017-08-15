from raffaello import Raffaello, parse_request

REQUEST = '''
error=>red
warning=>yellow_bold
bluish\stext=>color026
'''

raffaello = Raffaello(parse_request(REQUEST))
print(raffaello.paint('Sample message with error, warning and a bluish text.'))
