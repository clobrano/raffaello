Raffaello - output colorizer
============================

Raffaello colorizes the output stream of any command-line tool (gcc/g++, cmake, dmesg, syslog, etc.), and make it easier to read.

Starting from version 1.3.0, Raffaello can be used as python module in another source code (see pynicom) and since *a picture is worth a thousand words* and more pictures are even better, here are some examples.

### GCC/G++

![gcc](./examples/make.gif)

### DMSG

![dmesg](./examples/dmesg.gif)


## Usage

The raffaello's command line interface let you use two call modes: **pipes** and **command**.

In pipe mode you call raffaello like:

    <output stream source> | raffaello [options]

In command mode raffaello will call your stream source in your behalf

    raffaello [options] -c <output stream source>


Raffaello can use 2 color modes, 2 styles modes

**8 colors** mode let you use the following names: black, red, green, yellow, blue, magenta, cyan, light_gray

**256 colors** mode let you use other 248 colors and choose between foreground or background colors (you can mix 8 colors mode names with 256 color mode names):

    * Foreground color names are in the form 'colorNUM'. E.g. foreground red is color001
    * Background color names are in the form 'bgcolorNUM'. E.g. background red is bgcolor001

With styles you can blend colors in **bold** and **underlined**

    * foreground red bold is color001_bold
    * foreground red underlined is color001_underlined

Call `raffaello -l` to see the complete list of available colors.


### Full interface description

raffaello (-p PRESET | -r REQUEST | -f FILE | -l) [options]

    -p PRESET, --preset=PRESET              Prebuilt config files for coloring known output streams (cmake, gcc/g++, dmesg, cppcheck, at command, nmea, etc.)
    -r REQUEST --request=REQUEST            The requested text=>color mapping string. Multipe requests are separated by a space. Regular expression are supported. E.g. "error=>red [Ww]arning=>yellow_bold".
    -f FILE --file=FILE                     Path to a custom text=>color configuration file. Custom configuration files can include other custom files as well as built-in presets.
    -c COMMAND --command=COMMAND            Instead of using raffaello with pipes, set the command-line tool to be executed by raffaello directly. E.g. -c "dmesg -w".
    -d DELIMITER --delimiter=DELIMITER      If you don't like "=>" as delimiter between text and color, use this flag to change it. E.g. -d & [default: =>]
    -l, --list                              List all the available colors and presets
    -v --verbose                            Enable debug logging


## Examples

The simpler usage is using the `request` flag. The `request` flag requires a string in the form "text=>color", where text can be a constant string or a [Regular expression](https://docs.python.org/2/library/re.html), while color is the name of the color to use (see [Usage](#Usage) section)

* Simple constant text highlight

    $ ifconfig eno1 | raffaello --request="collisions=>blue"
    
![example001](./examples/raffaello001.png)

* Highlight of multiple texts. Here you can see that spaces in the text are not allowed. Use \s instead.

    $ ifconfig eno1 | raffaello --request="RX\spackets=>green TX\spackets=>red"

![example002](./examples/raffaello002.png)

* Highlight with regular expressions

    $ ifconfig eno1 | raffaello --request="\d+\.\d+\.\d+\.\d+=>green_bold"

![example003](./examples/raffaello003.png)


For more complex color mapping you can write a file with a line for each text=>color entry, like the following

    collisions=>blue
    RX\spackets=>green
    TX\spackets=>red
    \d+\.\d+\.\d+\.\d+=>green_bold

save the file and provide it to raffaello using its fullpath

    $ ifconfig eno1 | raffaello --file=$HOME/colorfile

![example004](./examples/raffaello004.png)

Color files can be reused in other color files using the `include` directive followed by the fullpath to the file.

Using fullpath is annoying, tough, so Raffaello has a special path under $HOME/.raffaello. All the colorfiles inside this folder can be passed using simply their filename, without the path.

Raffaello provides some built-in colorfiles called **presets**. Presets can be included in a custom files, for a full list of presets, call `raffaello --list`

## Raffaello is a python module

Raffaello can be used as a python module inside other source codes

{% highlight python %}
from raffaello import Raffaello, Commission

request = '''
error=>red
warning=>yellow_bold
bluish\stext=>color026
'''

c = Commission(request)
r = Raffaello(c.commission)

print(r.paint('Sample message with error, warning and a bluish text.'))
{% endhighlight %}

## Install

Install from source using setuptools. Just type the following command

    # python setup.py install

Install from [PyPI - the Python Package Index](https://pypi.python.org/pypi)

    # pip install raffaello


## Dependencies

* `docopt` language for description of command-line interfaces
