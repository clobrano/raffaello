# Raffaello

Raffaello is a command line (CLI) output colorizer

Usage:

	./raffaello <arguments> --- command [arguments]

Raffaello needs to be configured to colorize the CLI output.

Configuration can be provided direclty through command line with arguments:

	.$ /raffaello "pattern1==colorA" "pattern2==colorB" "pattern3==colorA" ... --- command [arguments]

	e.g.

		$ ./raffaello "\d+\.\d+==blue" --- dmesg	# this will make dmesg numbers blue
		$ ./raffaello '.*[Ee]rror.*==red' --- dmesg	# this will highlight lines with error messages (if any) in red


Configuration can also be provided through a config file like the following

	$ ./raffaello file=dmesg.cfg --- dmesg


	$ cat dmesg.cfg

	# Dmesg config file example. Comment lines will be ignored
	.*[Ee]rror.*==red_bold
	.*ERROR.*==red_bold
	timed\sout==red
	.*[Ww]arning.*==yellow

Notes:

	1. no spaces are allowed at both sides of == sign
	
		error == red		WRONG
		error== red		WRONG
		error ==red		WRONG
		error==red		OK
	2. if a pattern contains spaces, they must be defined using "\s" symbol, for example:
	
		could not==red_bold	WRONG
		could\snot==red_bold	OK


