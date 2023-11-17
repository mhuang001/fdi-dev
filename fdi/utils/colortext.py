# -*- coding: utf-8 -*-

"""
  to use::

     from fdi.utils.colortext import colortext

"""


from colorama import init, just_fix_windows_console, Fore, Back, Style

import curses
import functools
import logging

logger = logging.getLogger(__name__)

NOT_INITIALIZED = True

can = False
if NOT_INITIALIZED:
    #curses.initscr()
    init(autoreset=True)
    NOT_INITIALIZED = False
    can = True # curses.can_change_color()
    logger.info('Color text initialized successfully.')

...#just_fix_windows_console()

TEMPL = "\033[%s%dsm"


"""
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
"""
@ functools.lru_cache(maxsize=32)
def ctext(fore, back='BLACK', style='NORMAL'):
    global can
    if can:
        v = [getattr(Fore, fore.upper())]
        if back is not None:
            v.append(getattr(Back, back.upper()))
        if style is not None:
            v.append(getattr(Style, style.upper()))
            
        return ''.join(v)

# to use: print(f'{_BLACK_RED}Hello World!')
_BLUE = ctext('blue', back=None, style=None)
_BLUE_DIM = ctext('blue', back=None, style='dim')
_CYAN = ctext('cyan', back=None, style='bright')
_MAGENTA = ctext('magenta', back=None, style='bright')
_MAGENTA_DIM = ctext('magenta', back=None, style='dim')
_RED = ctext('red', back=None, style='bright')
_WHITE = ctext('white', back=None, style=None)
_BLACK_RED = ctext('black', back='red', style=None)
_YELLOW = ctext('yellow', back=None, style='bright')
_YELLOW_RED = ctext('lightyellow_ex', back='red', style='bright')
_HIWTE_RED = ctext('white', back='red', style='bright')
_RESET = Style.RESET_ALL

# loging.logger text
COLORS = {
    "CRITICAL": Fore.YELLOW,
    "ERROR": Fore.RED,
    "WARNING": Fore.YELLOW,
    "INFO": Fore.GREEN,
    "DEBUG": Fore.BLUE,
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, *, format, use_color=True):
        logging.Formatter.__init__(self, fmt=format)
        self.use_color = use_color

    def format(self, record):
        msg = super().format(record)
        if self.use_color:
            levelname = record.levelname
            if hasattr(record, "color"):
                return f"{record.color}{msg}{Style.RESET_ALL}"
            if levelname in COLORS:
                return f"{COLORS[levelname]}{msg}{Style.RESET_ALL}"
        return msg


