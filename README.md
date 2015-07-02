Raffaello
=========

What is it?
-----------

Raffaello is a powerful yet simple to use command line (CLI) output colorizer. What does that mean?
Let say you have a CLI tool that prints out lot of information you have to read carefully (gcc, g++, dmesg, etc.), how hard is that? And how easier would it be if some keywords were highlighted with meaningful colors? Well, Raffaello does just that.

Since *a picture is worth a thousand words* and more pictures are even better, here are some examples.

### GCC/G++

![gcc](./examples/make.gif)

### DMSG

![dmesg](./examples/dmesg.gif)

### IFCONFIG


The following is an example of **conditional hightlightning** make it possible by regular expressions.

`ifconfig` reports the number of errors in packets RX and TX and I wanted to highlight the word "errors" only when actual errors have occurred.

This is the pattern

    (errors):[1-9]=>red_bold

this way, strings like `*errors:0"` are not highlighted and I do not get false warnings.

![ifconfig](./examples/ifconfig.gif)


## Installation

`Raffaello` is simple to install using `setuptools`. Just type the following command

    # python setup.py install


## Usage

### Command line

`Raffaello` is simple to use. It just needs to know which **keywords** you want to colorize ([regular expressions](https://docs.python.org/2/library/re.html) using Python syntax are possible) and which **colors**.

The basic syntax is the following:

    raffaello <arguments> --- command-line-tool [command-line-tool-arguments]

OR using **pipe**

    command-line-tool [command-line-tool-arguments] | raffaello <arguments>


Color **configuration** can be provided **direclty through command line** with arguments:

    $ raffaello "pattern1=>colorA" "pattern2=>colorB" "pattern3=>colorA" ... --- command [arguments]

    e.g.

        $ raffaello "error=>red" "Error=>red" --- dmesg     # this will highlight the word error in a messages in red
        $ raffaello '[Ee]rror=>red' --- dmesg               # this does the same highlight but with regex

**Configuration** can also be provided **through a config file** like the following

    $ raffaello --file=dmesg.cfg --- dmesg
    $ dmesg | raffaello --file=dmesg.cfg

where configuration file is

    $ cat dmesg.cfg

    # Dmesg config file example. Comment lines will be ignored
    .*[Ee]rror.*=>red_bold
    .*ERROR.*=>red_bold
    timed\sout=>red
    .*[Ww]arning.*=>yellow


Note that:

    1. no spaces are allowed at both sides of `=>` sign
        error => red            WRONG
        error=> red             WRONG
        error =>red             WRONG
        error=>red              OK
    2. if a pattern contains spaces, they must be defined using "\s" symbol, for example:
        could not=>red_bold     WRONG
        could\snot=>red_bold    OK

To **avoid long file paths**, it is possible to put your config files under `<HOME>/.raffaello` hidden directory.

### Python module

Since version 1.3.0, Raffaello can be used as python module in a source code.

Once imported the module, use `raffaello.parse_color_option` or `raffallo.parse_config_file` to get the color configuration, and then use `raffaello.paint (<string>, configuration)` to apply the color codes to your text.

e.g.

    import readline
    configuration = readline.parse_color_option ('this=>red')
    print (readline.paint ('I want to parse this', configuration))


