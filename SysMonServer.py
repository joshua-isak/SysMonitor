import time
import curses
from curses import wrapper
import socket
import struct

VERSION = "0.1"

# Some colors as ANSI Escape codes for terminal output
class Color:
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    cyan = '\033[96m'
    end = '\033[0m'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Packet handling
class Packet:
    pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Object class for connected monitor clients
class Monitor:
    def __init__(self):
        # Static variables
        self.hostname = None
        self.ip_address = None
        self.os = None
        self.ram_total = None

        # Dynamic variables
        self.status = None
        self.uptime = None
        self.cpu_usage = None
        self.ram_usage = None


        self.last_contact = 0


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Object class for TUI Display
class Display:
    def __init__(self, scr):
        self.scr = scr

        # Init curses output
        scr.clear()
        scr.addstr(0, 0, "SysMonitor Dashboard v" + VERSION)  # Version Info
        scr.addstr(3, 0, "Initializing Server...")                          
        scr.refresh()

    def editLine(self, y, x, string):
        self.scr.addstr(y, x, string)

    def updateTime(self): # Update the time
        datetime = time.strftime("%Y-%m-%d    %H:%M:%S", time.gmtime())
        self.scr.addstr(3, 0, datetime)
        self.scr.refresh()

    def updateConnectedHosts(self):
        pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def getUptime(): # Get system uptime and return a tuple (days, hours, minutes)
    seconds = time.time() #psutil.boot_time()
    minute, sec = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)
    
    return day, hour, minute


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def main(scr=""):
    # Variables
    running = True                  # parallel threads will rejoin if this is false
    monitor_ids = []                # an array containing the ids of monitors linked to this server
    monitors = {}                   # A dictionary matching monitor ids to their object class reference


    # Init curses output
    curse = Display(scr)

    # Set up socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 4296))

    curse.updateTime()
    time.sleep(1)
    curse.updateTime()
    time.sleep(1)
    curse.updateTime()
    time.sleep(1)
    curse.updateTime()
    time.sleep(1)

    time.sleep(1)




# Run the main program in a wrapper so curses plays nice with the terminal...
# TODO add option to disable using curses if running the server in headless mode
wrapper(main)

#run headless
#main()