import socket
import time
import psutil
import struct

import platform
from threading import Thread





class Buffer:       # A helper class to aid in writing data to packets
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
        os = os + " " + platform.release() + " v" + platform.version()

    elif(os == 'Darwin'):
        os = "TODO, IMPLEMENT MacOS"    #TODO, implement MacOS
    
    return os


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #    


def init_connection(connection, hostname, os, ram_total):     # Initialize the connection to the server
    packet = Buffer(256)            # Create a new buffer of 512 bytes to hold outgoing packet data
    packet.prepare_packet(1)        # Packet type 1 is for initial connections from clients

    # Packet Structure: Padding>Packet_Type>HostnameLen>Hostname>OsLen>OS>RamTotal
    
    # Write the hostname to the packet
    hostname_len = len(hostname)                # max is 255
    packet.write_real('B', 1, hostname_len)     # 'B' for unsigned char, 1 for # of bytes, last arg is data to write
    packet.write_string(hostname)

    # Write the os data to the packet
    os_len = len(os)
    packet.write_real('B', 1, os_len)
    packet.write_string(os)

    # Write the total ram to the packet
    packet.write_real('I', 4, ram_total)        # max is 4,294,967,295. 'I' for unsigned int, 4 bytes in size

    connection.socket.sendto(packet.data, connection.ip)                # send the packet to initialize the connection
    time.sleep(4)

    try:
        data, ip = connection.socket.recvfrom(1024)      # return the server's response (when it arrives)
        connection.received_data = data
        connection.ip = ip
    except BlockingIOError:
        return 0


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def send_update():
    pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


class WatchdogServer:               # Watchdog server object
    def __init__(self, ip, port):
        self.ip = (ip, port)
        self.received_data = bytearray(5)

        # Set up UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # configure socket for ipv4 and UDP#
        self.socket.bind(("", 4296))                                    # "" means socket will listen to any network source on port 4296
        self.socket.setblocking(0)                                      # so the program doesn't hang during socket.recv


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #



def main():
    print("Initializing...")

    # Network Variables
    IP = "zeus.joshuaisak.com"
    PORT = 4296
    
    # Init (relatively) static variables
    hostname = socket.gethostname()     # Hostname
    os = getOS()                        # Operating System
    ram_total = 0                       # Total available RAM

    # Dynamic variables
    uptime = psutil.boot_time()                 # Uptime
    cpu_usage = psutil.cpu_percent()            # CPU Usage %
    ram_usage = psutil.virtual_memory().percent # RAM Usage %

    # Init connection to server
    print("Connecting to server...")
    connection = WatchdogServer(IP, PORT)           # Initialize connection object

    init_connection(connection, hostname, os, ram_total)                                                         

    if (struct.unpack('B', connection.received_data[1:2])[0] == 2):     # check for a value of 2 in the second byte of the returned packet
        print("Connected to {}:{} !".format( connection.ip[0], connection.ip[1] ))
    else:
        print("Connection to server failed.")            
        return 0                                        # terminate main() if bad data is received



main()


# Get (hopefully) static variables

#hostname = socket.gethostname()     # Hostname
#cpu_usage = psutil.cpu_percent()

#time.sleep(0.1)

#cpu_usage = psutil.cpu_percent()

# Test variables
#print(hostname)
#CPU USAGE
#print(str(cpu_usage) + "%")

# logical cpu count
#print(psutil.cpu_count())


#print(psutil.disk_usage('/'))

#UPTIME
#print(psutil.boot_time())

#RAM
#print(psutil.virtual_memory().percent)
