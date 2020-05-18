import socket
import time
import psutil
import struct
import sys

import platform
from threading import Thread





class Buffer:       # A helper to aid in writing data to packets
    def __init__(self, size=128):
        self.data = bytearray(size)
        self.offset = 0

    def prepare_packet(self, packet_type):
        struct.pack_into('BB', self.data, self.offset, 0, packet_type)
        self.offset += 2

    def write_real(self, real_type, type_bytesize, value):
        fmt = '<' + real_type
        struct.pack_into(fmt, self.data, self.offset, value)
        self.offset += type_bytesize

    def write_string(self, string):
        string = string.encode('utf-8')
        fmt = str(len(string)) + 's'
        struct.pack_into(fmt, self.data, self.offset, string)
        self.offset += len(string)
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #  


def getOS():    # Get OS information+
    os = platform.system()  

    if (os == 'Linux'):
        import distro   #should automatically be included on python running on linux (I think?)
        linux_info = distro.linux_distribution()    # get a tuple of information about the linux distro
        os = linux_info[0] + " " + linux_info[1] + " " + linux_info[2]

    elif (os == 'Windows'):
        os = os + " " + platform.release() #+ " v" + platform.version()

    elif(os == 'Darwin'):
        os = "OSX " + platform.mac_ver()[0]
    
    return os

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - # 


def send_packet(data, connection):
    try:
        connection.socket.sendto(data, connection.ip)
    except:
        pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #    


def init_connection(connection, hostname, os, ram_total, mobile):     # Initialize the connection to the server
    packet = Buffer(256)            # Create a new buffer of 256 bytes to hold outgoing packet data
    packet.prepare_packet(1)        # Packet type 1 is for initial connections from clients

    # Packet Structure: Padding>Packet_Type>HostnameLen>Hostname>OsLen>OS>RamTotal>BatteryPercent
    
    # Write the hostname to the packet
    hostname_len = len(hostname)                # max is 255
    packet.write_real('B', 1, hostname_len)     # 'B' for unsigned char, 1 for # of bytes, last arg is data to write
    packet.write_string(hostname)

    # Write the os data to the packet
    os_len = len(os)
    packet.write_real('B', 1, os_len)
    packet.write_string(os)

    # Write the total ram to the packet
    packet.write_real('I', 4, ram_total)        # max value is 4,294,967,295. 'I' for unsigned int, 4 bytes in size

    # Write the battery percentage (if applicable)
    if (mobile):
        battery = psutil.sensors_battery()[0]
        packet.write_real('B', 1, battery)

    #connection.socket.sendto(packet.data, connection.ip)                # send the packet to initialize the connection
    send_packet(packet.data, connection)

    time.sleep(4)           # Wait 4 seconds then check for a response

    try:
        data, ip = connection.socket.recvfrom(1024)      # return the server's response (when it arrives)
    except BlockingIOError:
        return 0

    connection.received_data = data     # Padding>Packet_Type>client_id
    connection.ip = ip

    # handle the received_data (read in our client id)
    connection.client_id = struct.unpack('B', data[2:3])[0]

    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def send_update(connection, mobile):
    # Get some system status updates
    uptime = int(psutil.boot_time())            # Uptime (But really boot_time) needs to be cast to an int cuz psutil returns a float
    cpu_usage = psutil.cpu_percent()            # CPU Usage %
    ram_usage = psutil.virtual_memory().percent # RAM Usage %
    if (mobile):
        battery = psutil.sensors_battery()[0]   # Battery %
    else:
        battery = 0

    packet = Buffer(256)            # Create a new buffer of 256 bytes to hold outgoing packet data
    packet.prepare_packet(3)        # Packet type 3 is for updates sent from clients  

    # Packet Structure: Padding>Packet_Type>client_id>uptime>cpu_usage>ram_usage>BatteryPercent

    # Write in this client's id
    packet.write_real('B', 1, connection.client_id)     # 'B' for unsigned char, 1 for # of bytes

    # Write some status updates
    packet.write_real('I', 4, uptime)                   # 'I' for unsigned int, 4 for # of bytes, last arg is data to write
    packet.write_real('f', 4, cpu_usage)                # 'f' for float, 4 for # of bytes
    packet.write_real('f', 4, ram_usage)

    packet.write_real('B', 1, battery)             

    # Send the packet to the server
    #connection.socket.sendto(packet.data, connection.ip)
    send_packet(packet.data, connection)
    #print("Sent status update")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


class WatchdogServer:               # Watchdog server object
    def __init__(self, ip, port):
        self.ip = (ip, port)
        self.received_data = bytearray(5)
        self.client_id = 0

        # Set up UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # configure socket for ipv4 and UDP#
        self.socket.bind(("", port))                                    # "" means socket will listen to any network source on port 4296
        self.socket.setblocking(0)                                      # so the program doesn't hang during socket.recv


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #



def main():

    # Get arguments for IP and PORT from command line
    try:
        IP = str(sys.argv[1])
        PORT = int(sys.argv[2])
        MOBILE = int(sys.argv[3])   # 1 or 0 (1 being this client has a battery)
    except:
        print("[*] Usage: python3 SysMonClient.py <IP> <PORT> <MOBILE>")
        sys.exit()

    print("Initializing...")

    # Network Variables
    #IP = "zeus.joshuaisak.com"
    #PORT = 4296
    UPDATE_INTERVAL = 2     # How many seconds to wait between sending status updates to the server
    
    # Init (relatively) static variables
    hostname = socket.gethostname()     # Hostname
    os = getOS()                        # Operating System
    ram_total = 0                       # Total available RAM

    # Dynamic variables
    uptime = psutil.boot_time()                 # Uptime
    cpu_usage = psutil.cpu_percent()            # CPU Usage %
    ram_usage = psutil.virtual_memory().percent # RAM Usage %


    # Initialize connection to server
    print("Connecting to server...")
    connection = WatchdogServer(IP, PORT)           # Initialize connection object (the socket too!)

    init_connection(connection, hostname, os, ram_total, MOBILE)    # Contact the server and tell it this client's details

    # Packet type 2 is response from server to client's initial connection request
    if (struct.unpack('B', connection.received_data[1:2])[0] == 2):     # check for a value of 2 in the second byte of the returned packet
        print("Connected to {}:{}".format( connection.ip[0], connection.ip[1] ))
    else:
        print("Connection to server failed.")            
        return 0                                        # terminate main() if bad data is received

    # Send status updates to the server
    while True:
        time.sleep(UPDATE_INTERVAL)         # How long to wait between sending status updates
        send_update(connection, MOBILE)             # Get that status information and send it!




# You already know who it is
main()


# TODO Config File
# TODO Socket reset upon network change