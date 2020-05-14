import time
import curses
from curses import wrapper
import socket
import struct
from threading import Thread
import random

VERSION = "0.1"


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Packet handling
class Packet:
    def handle_initial_connection(self, server, packet_data, packet_ip):
        # Generate a new random uid that is not already in use and assign it to the new watchdog object
        while True:                                         
            new_id = random.randint(1, 255)
            if (new_id not in server.watchdogs.keys()):
                break

        new_watchdog = Watchdog()       # Declare the new watchdog object
        new_watchdog.id = new_id        # Set its new uid

        server.watchdogs[new_id] = new_watchdog     # Add this new watchdog object to the server's dictionary of watchdogs

        # Set the watchdog's Hostname (TODO This needs its own Buffer.unpack class and method or something)
        hostname_len = struct.unpack('B', packet_data[2:3])[0]      # Get the hostname's length
        fmt = str(hostname_len) + 's'                               # format for unpacking the hostname with struct
        end = 3 + hostname_len
        hostname = struct.unpack(fmt, packet_data[3:end])[0]        # unpack the hostname
        new_watchdog.hostname = hostname.decode('utf-8')            # set the watchdog object's hostname

        start = end     #last read's end becomes next read's start

        # Set the watchdog's os information
        end = start + 1
        os_len = struct.unpack('B', packet_data[start:end])[0]
        start = end

        fmt = str(os_len) + 's'
        end = start + os_len
        os = struct.unpack(fmt, packet_data[start:end])[0]
        new_watchdog.os = os.decode('utf-8')
        
        # screw the ram_total for now lol... TODO actually implement this
        new_watchdog.ram_total = 69420

        # set the ip address of the watchdog
        new_watchdog.ip_address = packet_ip[0]      # Packet ip is a tuple (ip, port), this sets the address to only the ip 


    def handle_watchdog_update(self):
        pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


class Server:               # where server variables live
    def __init__(self):
        self.socket = None
        self.running = True                   # parallel threads will rejoin if this is false
        #self.watchdog_ids = []               # an array containing the ids of watchdogs linked to this server
        self.watchdogs = {}                   # A dictionary matching watchdog ids to their object class reference

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Object class for connected watchdog clients
class Watchdog:
    def __init__(self):
        self.id = None

        # Static variables from watchdog client
        self.hostname = None
        self.ip_address = None
        self.os = None
        self.ram_total = None

        # Dynamic variables
        self.status = "Online"
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

        #curses.curs_set(0) # Hide the cursor!


    def editLine(self, y, x, string):
        self.scr.addstr(y, x, string)


    def updateTime(self): # Update the time
        date_time = time.strftime("%m-%d-%Y  %H:%M:%S", time.localtime())
        self.scr.addstr(2, 0, date_time)
        #self.scr.refresh()


    def updateConnectedNum(self, watchdogs):
        total_hosts = len(watchdogs)
        connected_hosts = 0
        #for x in watchdogs:
        #    if host = connected:
        #        connected_hosts += 1
        host_string = "{}/{} Host(s) Online    ".format(connected_hosts, total_hosts)
        self.scr.addstr(3, 0, host_string)
        #self.scr.refresh()


    def updateConnectedHosts(self, watchdogs):
        line = 5        # The current line to draw at

        # Draw information about each host as detailed in monitorGUI.test
        for z in watchdogs.values():
            string = "{} ({}) {}".format(z.hostname, z.status, z.ip_address)
            self.scr.addstr(line, 0, string)
            line += 1
            self.scr.addstr(line, 2, "OS:")
            self.scr.addstr(line, 13, z.os)
            line += 1
            self.scr.addstr(line, 2, "Uptime:")
            line += 1
            self.scr.addstr(line, 2, "CPU Usage:")
            line += 1
            self.scr.addstr(line, 2, "RAM Usage:")
            line += 2


    def displayUpdater(self, server):   # Thread to update the display every second
        while server.running:
            time.sleep(1)
            self.updateTime()
            self.updateConnectedNum(server.watchdogs)

            self.updateConnectedHosts(server.watchdogs)

            #self.scr.move(5, 0)
            self.scr.refresh()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def getUptime(boot_time): # Get system uptime and return a tuple (days, hours, minutes)
    seconds = time.time() - boot_time #psutil.boot_time()
    minute, sec = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)
    
    return day, hour, minute


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def main(scr=""):
    # Init server object
    server = Server()           # TODO move socket initialization into here

    # Init curses output
    curse = Display(scr)

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 4296))
    server.socket = sock

    # Set up display updater thread
    displayUpdaterThread = Thread(target=curse.displayUpdater, args=(server,))
    displayUpdaterThread.start()

    # packet handling loop
    while server.running:
        packet_data, packet_ip = sock.recvfrom(1024)   # get the data sent to the server

        # unpack part of the packet data to find the packet type
        packet_type = struct.unpack('B', packet_data[1:2])[0]

        # set up a thread to handle the packet type
        if (packet_type == 1):          # Initial Connection from watchdog
            t = Thread(target=Packet.handle_initial_connection, args=(None, server, packet_data, packet_ip))
            # None is needed as an arg to override the self arg because of the packet class    

        elif (packet_type == 3):          # Watchdog status update
            t = Thread(target=Packet.handle_watchdog_update, args=(None, server, packet_data))

        else:
            continue

        t.start()   # start the thread to handle the packet


    # No way to get down here with the above running in a loop eh?
    time.sleep(10)
    server.running = False





# Run the main program in a wrapper so curses plays nice with the terminal...
# TODO add option to disable using curses if running the server in headless mode
wrapper(main)

#run headless
#main()