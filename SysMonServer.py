import time
import curses
from curses import wrapper
import socket
import struct

VERSION = "0.1"


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Packet handling
class Packet:
    pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Object class for connected watchdog clients
class Watchdog:
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
        date_time = time.strftime("%m-%d-%Y  %H:%M:%S", time.localtime())
        self.scr.addstr(2, 0, date_time)
        self.scr.refresh()

    def updateConnectedNum(self, watchdogs):
        total_hosts = len(watchdogs)
        connected_hosts = 0
        #for x in watchdogs:
        #    if host = connected:
        #        connected_hosts += 1
        host_string = "{}/{} Host(s) Online    ".format(connected_hosts, total_hosts)
        self.scr.addstr(3, 0, host_string)
        self.scr.refresh()

    def updateConnectedHosts(self, watchdogs):
        pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def getUptime(boot_time): # Get system uptime and return a tuple (days, hours, minutes)
    seconds = time.time() - boot_time #psutil.boot_time()
    minute, sec = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)
    
    return day, hour, minute


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def main(scr=""):
    # Variables
    running = True                  # parallel threads will rejoin if this is false
    watchdog_ids = []                # an array containing the ids of watchdogs linked to this server
    watchdogs = {}                   # A dictionary matching watchdog ids to their object class reference


    # Init curses output
    curse = Display(scr)

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 4296))

    curse.updateConnectedNum(watchdogs)
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