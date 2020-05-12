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
        string.encode('utf-8')
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


def init_connection(sock, ip, hostname, os, ram_total):     # Initialize the connection to the server
    packet = Buffer(512)     # Create a new buffer of 512 bytes to hold outgoing packet data
    packet.prepare_packet(1)        # Packet type 1 is for initial connections from clients

    # Packet Structure: Padding>Packet_Type>HostnameLen>Hostname>OsLen>OS>RamTotal
    
    # Write the hostname to the packet
    hostname_len = len(hostname)                # max is 255
    packet.write_real('B', 1, hostname_len)     # 'B' for unsigned char, 1 for # of bytes, last arg is data to write
    packet.write_string(hostname_len)

    # Write the os data to the packet
    os_len = len(os)
    packet.write_real('B', 1, os_len)
    packet.write_string(os)

    # Write the total ram to the packet
    packet.write_real('I', 4, ram_total)        # max is 4,294,967,295. 'I' for unsigned int, 4 bytes in size

    sock.sendto(packet.data, ip)                # send the packet to initialize the connection

    time.sleep(4)       # wait 4 seconds for a response from the server

    pass

def send_update():
    pass



def main():
    print("Initializing...")

    # Network Variables
    IP = "zeus.joshuaisak.com"
    PORT = 4296
    ADDRESS = (IP, PORT)
    connected = False
    
    # Init (relatively) static variables
    hostname = socket.gethostname()     # Hostname
    os = getOS()                        # Operating System
    ram_total = 0                       # Total available RAM

    # Dynamic variables
    uptime = psutil.boot_time()                 # Uptime
    cpu_usage = psutil.cpu_percent()            # CPU Usage %
    ram_usage = psutil.virtual_memory().percent # RAM Usage %

    print("Connecting to server...")
    
    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # configure socket for ipv4 and UDP#
    sock.bind(("", 4296))                                   # "" means socket will listen to any network source on port 4296

    init_connection(sock, ADDRESS, hostname, os, ram_total) # set up connection to watchdog server


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
