# Raffaello

Raffaello is a command line (CLI) output colorizer.

## Installation

    # python setup.py install


## Usage

	raffaello <arguments> --- command [arguments]

## Examples

### Make

![make](./examples/make.gif)

### dmsg

![dmesg](./examples/dmesg.gif)

### ifconfig

The following is an example of "conditional" hightlightning. I wanted to highlight the word "errors" only when actual errors have occurred. This is the pattern

	(errors):[1-9]=>red_bold

this way, strings like *errors:0" are not highlighted and I do not get false warnings.

![ifconfig](./examples/ifconfig.gif)



## Configuration

Raffaello needs to be configured to colorize the CLI output.

Configuration can be provided direclty through command line with arguments:

	.$ /raffaello "pattern1=>colorA" "pattern2=>colorB" "pattern3=>colorA" ... --- command [arguments]

	e.g.

		$ ./raffaello "\d+\.\d+=>blue" --- dmesg	# this will make dmesg numbers blue
		$ ./raffaello '.*[Ee]rror.*=>red' --- dmesg	# this will highlight lines with error messages (if any) in red


Configuration can also be provided through a config file like the following

	$ ./raffaello --file=dmesg.cfg --- dmesg

where configuration file is

	$ cat dmesg.cfg

	# Dmesg config file example. Comment lines will be ignored
	.*[Ee]rror.*=>red_bold
	.*ERROR.*=>red_bold
	timed\sout=>red
	.*[Ww]arning.*=>yellow


	1. no spaces are allowed(1) at both sides of `=>` sign
		error => red	WRONG
		error=> red		WRONG
		error =>red		WRONG
		error=>red		OK
	2. if a pattern contains spaces, they must be defined using "\s" symbol, for example:
		could not=>red_bold		WRONG
		could\snot=>red_bold	OK
