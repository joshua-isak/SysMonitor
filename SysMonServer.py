import time
import curses
from curses import wrapper
import socket
import struct
from threading import Thread
import random
import sys

VERSION = "0.1"


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


class Buffer:       # A helper to aid in writing data to packets
    def __init__(self, size):
        self.data = bytearray(size)
        self.offset = 0

    def prepare_packet(self, packet_type):
        struct.pack_into('BB', self.data, self.offset, 0, packet_type)
        self.offset += 2

    def write_real(self, real_type, type_bytesize, value):
        fmt = '<' + real_type
        struct.pack_into(fmt, self.data, self.offset, value)
        self.offset += type_bytesize


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Packet handling
class Packet:
    def send_packet(self, server, packet_data, packet_ip):  # Send a packet containing packet_data to packet_ip
        server.socket.sendto(packet_data, packet_ip)    


    def handle_initial_connection(self, server, packet_data, packet_ip):
        # Generate a new random uid that is not already in use and assign it to the new watchdog object
        while True:                                         
            new_id = random.randint(1, 255)
            if (new_id not in server.watchdogs.keys()):
                break

        new_watchdog = Watchdog()       # Declare the new watchdog object
        new_watchdog.id = new_id        # Set its new uid

        server.watchdogs[new_id] = new_watchdog     # Add this new watchdog object to the server's dictionary of watchdogs

        # Packet Structure: Padding>Packet_Type>HostnameLen>Hostname>OsLen>OS>RamTotal>BatteryPercent

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
        
        start = end     # set start and end read variables for position of ram_total 4byte integer
        end = start + 4
        # screw the ram_total for now lol... TODO actually implement this
        new_watchdog.ram_total = 69420

        start = end     # set start and end read variables for position of battery 1byte char
        end = start + 1
        # get the battery percent if applicable
        battery = struct.unpack('B', packet_data[start:end])[0]
        new_watchdog.battery = battery

        # set the ip address of the watchdog
        new_watchdog.ip_address = packet_ip[0]          # Packet ip is a tuple (ip, port), this sets the address to only the ip

        # send a response to the watchdog client saying that their inital connection has been successfully processed
        new_packet = Buffer(64)
        new_packet.prepare_packet(2)                    # packet type 2 is for responses to the initial connection request
        new_packet.write_real('B', 1, new_watchdog.id)  # write the watchdog client's uid (which it will use when sending update communications)
 
        server.socket.sendto(new_packet.data, packet_ip)            # send the response


    def handle_watchdog_update(self, server, packet_data):
        # Packet Structure: Padding>Packet_Type>client_id>uptime>cpu_usage>ram_usage
        
        this_watchdog = struct.unpack('B', packet_data[2:3])[0]     # get the id of the client that sent this update

        if (this_watchdog not in server.watchdogs.keys()):          # stop the handle if the client id is invalid
            return 0

        this_watchdog = server.watchdogs[this_watchdog]             # get the watchdog object we want to update data for

        # Update the boot_time
        boot_time = struct.unpack('I', packet_data[3:7])[0]             # extract the unix time of the watchdog's boot
        this_watchdog.uptime = getTimeTuple(time.time() - boot_time)    # turn boot time into a tuple containing days, hours, minutes of uptime

        this_watchdog.cpu_usage = int( struct.unpack('f', packet_data[7:11])[0] )   # Update the CPU usage

        this_watchdog.ram_usage = int( struct.unpack('f', packet_data[11:15])[0] )  # Update the RAM usage

        this_watchdog.battery = int( struct.unpack('B', packet_data[15:16])[0] )    # Update the Battery percentage

        this_watchdog.last_contact = time.time()    # mark the time of last contact from the watchdog


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


class Server:               # where server variables live
    def __init__(self):
        self.socket = None
        self.running = True                   # parallel threads will rejoin if this is false
        self.watchdogs = {}                   # A dictionary matching watchdog ids to their object class reference
        self.online = 0                       # Number of watchdogs currently sending updates
        self.curse = None


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
        self.status = "Connecting"
        self.past_status = 0
        self.uptime = (0,0,0)
        self.cpu_usage = 0
        self.ram_usage = 0
        self.battery = 0

        self.last_contact = 0


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Object class for TUI Display
class Display:
    def __init__(self, scr):
        self.scr = scr
        self.to_clear = False

        # Init curses output
        scr.clear()
        scr.nodelay(1)                                          # makes getch() non-blocking
        scr.addstr(0, 0, "SysMonitor Dashboard v" + VERSION)    # Version Info
        scr.addstr(3, 0, "Initializing Server...")                          
        scr.refresh()

        #scr.border()    # draws a border around the terminal
        #curses.curs_set(0) # Hide the cursor!


    def editLine(self, y, x, string):
        self.scr.addstr(y, x, string)


    def updateTime(self): # Update the time
        date_time = time.strftime("%m-%d-%Y  %H:%M:%S", time.localtime())
        self.scr.addstr(2, 0, date_time)
        #self.scr.refresh()


    def updateConnectedNum(self, server):
        total_hosts = len(server.watchdogs)
        host_string = "{}/{} Host(s) Online   ".format(server.online, total_hosts)
        self.scr.addstr(3, 0, host_string)
        #self.scr.refresh()


    def updateConnectedHosts(self, watchdogs):
        line = 5        # The current line to draw at

        # Draw information about each host as detailed in monitorGUI.test
        for z in watchdogs.values():
            string = " {} ({}) {} ".format(z.hostname, z.status, z.ip_address)
            self.scr.addstr(line, 0, string, curses.A_REVERSE) # was UNDERLINE
            self.scr.touchline(line, 1)
            line += 1
            self.scr.addstr(line, 2, "OS:  " + z.os)
            #self.scr.addstr(line, 13, z.os)
            line += 1

            if (z.status == "Online"):
                # Update the uptime
                up_day = str(z.uptime[0])
                up_hour = str(z.uptime[1])
                up_min = str(z.uptime[2])

                day_plur, hour_plur, min_plur = "", "", ""    # handling for plural days, minutes...
                if (z.uptime[0] > 1):
                    day_plur = "s"
                if (z.uptime[1] > 1):
                    hour_plur = "s"
                if (z.uptime[2] > 1):
                    min_plur = "s"

                uptime = "{} day{}, {} hour{}, {} min{}  ".format(up_day, day_plur, up_hour, hour_plur, up_min, min_plur)
                self.scr.addstr(line, 2, "Uptime:  " + uptime)

                line += 1
                self.scr.addstr(line, 2, "CPU Usage:  " + str(z.cpu_usage) + "%  ")
                line += 1
                self.scr.addstr(line, 2, "RAM Usage:  " + str(z.ram_usage) + "%  ")

            elif (z.status == "Offline"):
                self.scr.addstr(line, 2, "Last seen: " + getTimeString(time.time() - z.last_contact))

            if (z.battery > 1):
                line += 1
                self.scr.addstr(line, 2, "Battery:  " + str(z.battery) + "%   ")

            line += 2


    def displayUpdater(self, server):   # Thread to update the display every second
        while server.running:
            time.sleep(1)

            if self.to_clear:
                self.scr.clear()    # clear the whole window
                self.scr.addstr(0, 0, "SysMonitor Dashboard v" + VERSION) # Version Info
                self.to_clear = False

            self.updateTime()
            self.updateConnectedNum(server)
            self.updateConnectedHosts(server.watchdogs)

            #self.scr.move(5, 0)
            self.scr.refresh()

            # stop the server if "Q" is pressed, send a packet looped back into the socket to break packet loop in main()
            ch = self.scr.getch()
            if (ch == ord('q')):            
                server.running = False
                server.socket.sendto("wow".encode('utf-8'), ("127.0.0.1", 4296))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def getTimeTuple(time): # Get system uptime and return a tuple (days, hours, minutes)
    seconds = time
    minute, sec = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)
    
    day = int(day)
    hour = int(hour)
    minute = int(minute)

    return (day, hour, minute)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def getTimeString(time):    # Return a string containing time as a string in the form day(s), hour(s), min(s)
    time = getTimeTuple(time)

    day = time[0]
    hour = time[1]
    minute = time[2]

    time_string = ""

    day_plur, hour_plur, min_plur = "", "", ""    # handling for plural days, minutes...
    if (day):
        if (day > 1):
            day_plur = "s"
        time_string += "{} day{}, ".format(str(day), day_plur)

    if (hour):
        if (hour > 1):
            hour_plur = "s"
        time_string += "{} hour{}, ".format(str(hour), hour_plur)

    if (minute > 1):
        min_plur = "s"
    elif (minute == 0):
        min_plur = "s"
    
    time_string += "{} minute{} ".format(str(minute), min_plur) + "ago"

    return time_string


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def connectionChecker(server):  # Checks if a watchdog hasn't reported in over 5 seconds and marks it offline
    while server.running:
        time.sleep(5)

        server.online = 0
        for x in server.watchdogs.values():
            if ((time.time() - x.last_contact) > 4):    # if the time of last contact is greater than 4 seconds
                # Change watchdog variables to reflect Offline status
                x.status = "Offline"
                x.cpu_usage = "-"
                x.ram_usage = "-"

                if x.past_status == 1:  # Check if there was a change in connection status, redraw the screen if so
                    x.past_status = 0
                    server.curse.to_clear = True

            else:
                x.status = "Online"     # if we have heard from the watchdog, set its status to online
                server.online += 1

                if x.past_status == 0:  
                    x.past_status = 1
                    server.curse.to_clear = True



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def main(scr=""):
    # Init server object
    server = Server()           # TODO move socket initialization into here

    # Init curses output
    curse = Display(scr)
    server.curse = curse

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 4296))
    server.socket = sock

    # Set up display updater thread
    displayUpdaterThread = Thread(target=curse.displayUpdater, args=(server,))
    displayUpdaterThread.start()

    # Set up ifconnected status thread
    connCheckThread = Thread(target=connectionChecker, args=(server,))
    connCheckThread.start()

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
    time.sleep(1)
    server.running = False
    print("Server shut down successfully")





# Run the main program in a wrapper so curses plays nice with the terminal...
# TODO add option to disable using curses if running the server in headless mode
wrapper(main)

#run headless
#main()