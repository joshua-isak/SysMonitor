import time
import curses
from curses import wrapper


# Some colors as ANSI Escape codes for terminal output
class color:
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    cyan = '\033[96m'
    end = '\033[0m'