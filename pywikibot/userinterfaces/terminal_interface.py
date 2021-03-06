# -*- coding: utf-8 -*-
#
# (C) Pywikipedia bot team, 2003-2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import traceback, re, sys
import logging
import threading
import pywikibot
from pywikibot import config
from pywikibot.bot import DEBUG, VERBOSE, INFO, STDOUT, INPUT, WARNING
from pywikibot.userinterfaces import transliteration


try:
    import ctypes
    ctypes_found = True
except ImportError:
    ctypes_found = False


def getDefaultTextColorInWindows():
    """
    This method determines the default text color and saves its color
    code inside the variable windowsColors['default'].

    Based on MIT-licensed code by Andre Burgaud published at
    http://starship.python.net/crew/theller/wiki/ColorConsole
    """
    if sys.platform != 'win32' or not ctypes_found:
        return -1
    SHORT = ctypes.c_short
    WORD = ctypes.c_ushort

    # wincon.h
    class COORD(ctypes.Structure):
        _fields_ = [
            ("X", SHORT),
            ("Y", SHORT)
        ]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [
            ("Left", SHORT),
            ("Top", SHORT),
            ("Right", SHORT),
            ("Bottom", SHORT)
        ]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", WORD),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD)
        ]

    std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(std_out_handle, ctypes.byref(csbi))
    return (csbi.wAttributes & 0x000f)

# TODO: other colors:
         #0 = Black
         #1 = Blue
         #2 = Green
         #3 = Aqua
         #4 = Red
         #5 = Purple
         #6 = Yellow
         #7 = White
         #8 = Gray
         #9 = Light Blue
        #10 = Light Green
        #11 = Light Aqua
        #12 = Light Red
        #13 = Light Purple
        #14 = Light Yellow
        #15 = Bright White

unixColors = {
    'default':     chr(27) + '[0m',     # Unix end tag to switch back to default
    'lightblue':   chr(27) + '[94;1m',  # Light Blue start tag
    'lightgreen':  chr(27) + '[92;1m',  # Light Green start tag
    'lightaqua':   chr(27) + '[36;1m',  # Light Aqua start tag
    'lightred':    chr(27) + '[91;1m',  # Light Red start tag
    'lightpurple': chr(27) + '[35;1m',  # Light Purple start tag
    'lightyellow': chr(27) + '[33;1m',  # Light Yellow start tag
}

windowsColors = {
    'default':     7,
    'black':       0,
    'blue':        1,
    'green':       2,
    'aqua':        3,
    'red':         4,
    'purple':      5,
    'yellow':      6,
    'lightgray':   7,
    'gray':        8,
    'lightblue':   9,
    'lightgreen':  10,
    'lightaqua':   11,
    'lightred':    12,
    'lightpurple': 13,
    'lightyellow': 14,
    'white':       15,
}

colorTagR = re.compile('\03{(?P<name>%s)}' % '|'.join(windowsColors.keys()))

class UI(object):
    def init_handlers(self, root_logger):
        """Initialize the handlers for user output.

        This method initializes handler(s) for output levels VERBOSE (if
        enabled by config.verbose_output), INFO, STDOUT, WARNING, ERROR,
        and CRITICAL.  STDOUT writes its output to sys.stdout; all the
        others write theirs to sys.stderr.

        """
        # default handler for display to terminal
        default_handler = TerminalHandler(strm=sys.stderr)
        if config.verbose_output:
            default_handler.setLevel(VERBOSE)
        else:
            default_handler.setLevel(INFO)
        # this handler ignores levels above INPUT
        default_handler.addFilter(MaxLevelFilter(INPUT))
        default_handler.setFormatter(
            TerminalFormatter(fmt="%(message)s%(newline)s"))
        root_logger.addHandler(default_handler)

        # handler for level STDOUT
        output_handler = TerminalHandler(strm=sys.stdout)
        output_handler.setLevel(STDOUT)
        output_handler.addFilter(MaxLevelFilter(STDOUT))
        output_handler.setFormatter(
            TerminalFormatter(fmt="%(message)s%(newline)s"))
        root_logger.addHandler(output_handler)

        # handler for levels WARNING and higher
        warning_handler = TerminalHandler(strm=sys.stderr)
        warning_handler.setLevel(logging.WARNING)
        warning_handler.setFormatter(
            TerminalFormatter(fmt="%(levelname)s: %(message)s%(newline)s"))
        root_logger.addHandler(warning_handler)

    def input(self, question, password = False):
        """
        Ask the user a question and return the answer.

        Works like raw_input(), but returns a unicode string instead of ASCII.

        Unlike raw_input, this function automatically adds a space after the
        question.
        """

        # sound the terminal bell to notify the user
        if config.ring_bell:
            sys.stdout.write('\07')

        # While we're waiting for user input,
        # we don't want terminal writes from other Threads
        TerminalHandler.sharedlock.acquire()
        try:
            pywikibot.logoutput(question + ' ', newline=False,
                                _level=pywikibot.INPUT)
            if password:
                import getpass
                text = getpass.getpass('')
                # See PYWP-13 / http://bugs.python.org/issue11236
                # getpass does not always raise an KeyboardInterrupt when ^C
                # is pressed.
                if '\x03' in text:
                    raise KeyboardInterrupt()
            else:
                text = raw_input()
        finally:
            TerminalHandler.sharedlock.release()

        if not isinstance(text, unicode):
            text = unicode(text, config.console_encoding)
        return text

    def inputChoice(self, question, options, hotkeys, default=None):
        """
        Ask the user a question with a predefined list of acceptable answers.
        """
        options = options[:] # we don't want to edit the passed parameter
        for i in range(len(options)):
            option = options[i]
            hotkey = hotkeys[i]
            # try to mark a part of the option name as the hotkey
            m = re.search('[%s%s]' % (hotkey.lower(), hotkey.upper()), option)
            if hotkey == default:
                caseHotkey = hotkey.upper()
            else:
                caseHotkey = hotkey
            if m:
                pos = m.start()
                options[i] = '%s[%s]%s' % (option[:pos], caseHotkey, option[pos+1:])
            else:
                options[i] = '%s [%s]' % (option, caseHotkey)

        answer = ''

        # loop until the user entered a valid choice
        while True:
            prompt = '%s (%s)' % (question, ', '.join(options))

            # it's okay to enter input with the lock, RLock is reentrant.
            answer = self.input(prompt)
            if answer.lower() in hotkeys or answer.upper() in hotkeys:
                break
            elif default and answer=='':		# empty string entered
                answer = default
                break
        return answer

    def editText(self, text, jumpIndex = None, highlight = None):
        """Return the text as edited by the user.

        Uses a Tkinter edit box because we don't have a console editor

        Parameters:
            * text      - a Unicode string
            * jumpIndex - an integer: position at which to put the caret
            * highlight - a substring; each occurence will be highlighted

        """
        try:
            import gui
        except ImportError, e:
            print 'Could not load GUI modules: %s' % e
            return text
        editor = gui.EditBoxWindow()
        return editor.edit(text, jumpIndex=jumpIndex, highlight=highlight)

    def askForCaptcha(self, url):
        """Show the user a CAPTCHA image and return the answer."""
        try:
            import webbrowser
            pywikibot.output(u'Opening CAPTCHA in your web browser...')
            webbrowser.open(url)
            return pywikibot.input(
                u'What is the solution of the CAPTCHA that is shown in your web browser?')
        except:
            pywikibot.output(u'Error in opening web browser: %s'
                              % sys.exc_info()[0])
            return pywikibot.input(
                u'What is the solution of the CAPTCHA at %s ?' % url)


class TerminalHandler(logging.Handler):
    """A handler class that writes logging records, appropriately formatted, to
    a stream connected to a terminal. This class does not close the stream,
    as sys.stdout or sys.stderr may be (and usually will be) used.

    Slightly modified version of the StreamHandler class that ships with
    logging module, plus code for colorization of output.

    """

    # create a class-level lock that can be shared by all instances
    import threading
    sharedlock = threading.RLock()

    def __init__(self, strm=None):
        """Initialize the handler.

        If strm is not specified, sys.stderr is used.

        """
        logging.Handler.__init__(self)
        # replace Handler's instance-specific lock with the shared class lock
        # to ensure that only one instance of this handler can write to
        # the console at a time
        self.lock = TerminalHandler.sharedlock
        if strm is None:
            strm = sys.stderr
        self.stream = strm
        self.formatter = None

    def flush(self):
        """Flush the stream. """
        self.stream.flush()

    def emit_raw(self, record, msg):
        """Emit a formatted message.

        The message is written to the stream. If exception information is
        present, it is formatted using traceback.print_exception and
        appended to the stream.

        """
        try:
            fs = "%s"
            if isinstance(msg, str):
                self.stream.write(fs % msg)
            else:
                try:
                    self.stream.write(fs % msg.encode(config.console_encoding,
                                                      "xmlcharrefreplace"))
                except UnicodeError:
                    self.stream.write(fs % msg.encode("ascii",
                                                      "xmlcharrefreplace"))
                self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def emitColorizedInUnix(self, record, msg):
        lastColor = None
        for key, value in unixColors.iteritems():
            msg = msg.replace('\03{%s}' % key, value)
        # just to be sure, reset the color
        msg += unixColors['default']
        self.emit_raw(record, msg)

    def emitColorizedInWindows(self, record, msg):
        """This only works in Python 2.5 or higher."""
        if ctypes_found:
            std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
            # Color tags might be cascaded, e.g. because of transliteration.
            # Therefore we need this stack.
            colorStack = []
            tagM = True
            while tagM:
                tagM = colorTagR.search(msg)
                if tagM:
                    # print the text up to the tag.
                    self.emit_raw(record, msg[:tagM.start()])
                    newColor = tagM.group('name')
                    if newColor == 'default':
                        if len(colorStack) > 0:
                            colorStack.pop()
                            if len(colorStack) > 0:
                                lastColor = colorStack[-1]
                            else:
                                lastColor = 'default'
                            ctypes.windll.kernel32.SetConsoleTextAttribute(
                                std_out_handle, windowsColors[lastColor])
                    else:
                        colorStack.append(newColor)
                        # set the new color
                        ctypes.windll.kernel32.SetConsoleTextAttribute(
                            std_out_handle, windowsColors[newColor])
                    msg = msg[tagM.end():]
            # print the rest of the text
            self.emit_raw(record, msg)
            # just to be sure, reset the color
            ctypes.windll.kernel32.SetConsoleTextAttribute(
                std_out_handle, windowsColors['default'])
        else:
            # ctypes is only available since Python 2.5, and we won't
            # try to colorize without it. Instead we add *** after the text
            # as a whole if anything needed to be colorized.
            lines = msg.split('\n')
            for line in lines:
                line, count = colorTagR.subn('', line)
                if count > 0:
                    line += '***'
                line += '\n'
                self.emit_raw(record, line)

    def emit(self, record):
        text = self.format(record)
        if config.transliterate:
            # Encode unicode string in the encoding used by the user's console,
            # and decode it back to unicode. Then we can see which characters
            # can't be represented in the console encoding.
            codecedText = text.encode(config.console_encoding, 'replace'
                                      ).decode(config.console_encoding)
            transliteratedText = list(codecedText)
            # Note: A transliteration replacement might be longer than the
            # original character; e.g., ч is transliterated to ch.
            # the resulting list will have as many elements as there are
            # characters in the original text, but some list elements may
            # contain multiple characters
            prev = "-"
            prevchar = -1
            cursor = 0
            while cursor < len(codecedText):
                char = codecedText.find(u"?", cursor)
                if char == -1:
                    break
                cursor = char + 1
                # work on characters that couldn't be encoded, but not on
                # original question marks.
                if text[char] != u"?":
                    if char > 0 and prevchar != char - 1:
                        prev = transliteratedText[char-1]
                    try:
                        transliterated = transliteration.trans(
                                             text[char], default='?',
                                             prev=prev, next=text[char+1])
                    except IndexError:
                        transliterated = transliteration.trans(
                                             text[char], default='?',
                                             prev=prev, next=' ')
                    # transliteration was successful. The replacement
                    # could consist of multiple letters.
                    # mark the transliterated letters in yellow.
                    transliteratedText[char] = u'\03{lightyellow}%s\03{default}' \
                                                % transliterated
                    # save the last transliterated character
                    prev = transliterated[-1:]
                    prevchar = char
            text = u"".join(transliteratedText)
        if config.colorized_output:
            if sys.platform == 'win32':
                self.emitColorizedInWindows(record, text)
            else:
                self.emitColorizedInUnix(record, text)
        else:
            self.emit_raw(record, text)


class TerminalFormatter(logging.Formatter):
    pass


class MaxLevelFilter(logging.Filter):
    """Filter that only passes records at or below a specific level.

    (setting handler level only passes records at or *above* a specified level,
    so this provides the opposite functionality)

    """
    def __init__(self, level=None):
        self.level = level

    def filter(self, record):
        if self.level:
            return record.levelno <= self.level
        else:
            return True
