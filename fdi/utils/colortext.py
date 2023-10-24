# -*- coding: utf-8 -*-

"""
  to use::

     from fdi.utils.colortext import colortext

"""


from colorama import init, just_fix_windows_console, Fore, Back, Style

import curses
import functools
import logging

just_fix_windows_console()

TEMPL = "\033[%s%dsm"
can = True #curses.can_change_color()

NOT_INITIALIZED = True

if NOT_INITIALIZED:
    init(autoreset=True)

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


