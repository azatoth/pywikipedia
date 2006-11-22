
__version__ = '$Id$'

import config, re, sys, transliteration

# TODO: other colors
unixColors = {
    None: chr(27) + '[0m',     # Unix end tag to switch back to default
    10:   chr(27) + '[92;1m',  # Light Green start tag
    12:   chr(27) + '[91;1m',  # Light Red start tag
}
class UI:
    def __init__(self):
        pass

    def output(self, text, colors = None, newline = True):
        """
        If a character can't be displayed in the encoding used by the user's
        terminal, it will be replaced with a question mark.

        colors is a list of integers, one for each character of text. If a
        list entry is None, the default terminal color will be used for the
        character at that position.

         0 = Black
         1 = Blue
         2 = Green
         3 = Aqua
         4 = Red
         5 = Purple
         6 = Yellow
         7 = White
         8 = Gray
         9 = Light Blue
        10 = Light Green
        11 = Light Aqua
        12 = Light Red
        13 = Light Purple
        14 = Light Yellow
        15 = Bright White
        """
        # don't know how to colorize in a win32 command shell
        newtext = ''
        if colors and config.colorized_output:
            lastColor = None
            for i in range(0, len(colors)):
                if colors[i] != lastColor:
                    # add an ANSI escape character
                    newtext += unixColors[colors[i]]
                # append one text character
                newtext += text[i]
                lastColor = colors[i]
            if lastColor != None:
                # reset the color to default at the end
                newtext += unixColors[None]
        else:
            newtext = text
        newtext = [letter.encode(config.console_encoding, 'replace') for letter in newtext]
        if config.transliterate:
            change = False
            for i in xrange(len(newtext)):
                if newtext[i] == '?':
                    newtext[i] = transliteration.trans(text[i],default = '?')
                    if newtext[i] != '?':
                        change = True
            if change:
                newtext.append('***')
        newtext = "".join(newtext)
        if newline:
            try:
                print newtext
            except: # For example, if there is a character that is transliterated to a non-encoded character
                print text.encode(config.console_encoding, 'replace')
        else:
            # comma at the end means "don't print newline"
            try:
                print newtext,
            except:
                print text.encode(config.console_encoding, 'replace'),

    def input(self, question):
        """
        Works like raw_input(), but returns a unicode string instead of ASCII.

        Unlike raw_input, this function automatically adds a space after the
        question.
        """

        # sound the terminal bell to notify the user
        if config.ring_bell:
            sys.stdout.write('\07')
        self.output(question, newline=False)
        text = raw_input()
        text = unicode(text, config.console_encoding)
        return text

    def inputChoice(self, question, options, hotkeys, default = None):
        for i in range(len(options)):
            option = options[i]
            hotkey = hotkeys[i]
            m = re.search('[%s%s]' % (hotkey.lower(), hotkey.upper()), option)
            if m:
                pos = m.start()
                options[i] = '%s[%s]%s' % (option[:pos], hotkey, option[pos+1:])
            else:
                options[i] = '%s [%s]' % (option, hotkey)
        while True:
            prompt = '%s (%s)' % (question, ', '.join(options))
            answer = self.input(prompt)
            if answer.lower() in hotkeys or answer.upper() in hotkeys:
                return answer.lower()
            elif default and answer=='':		# empty string entered
                return default

    def editText(self, text, jumpIndex = None, highlight = None):
        """
        Uses a Tkinter edit box because we don't have a console editor
        
        Parameters:
            * text      - a Unicode string
            * jumpIndex - an integer: position at which to put the caret
            * highlight - a substring; each occurence will be highlighted
        """
        import gui
        editor = gui.EditBoxWindow()
        return editor.edit(text, jumpIndex = jumpIndex, highlight = highlight)
