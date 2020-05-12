import socket
import time
import psutil

import platform
from threading import Thread



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #  

def getOS():    # Get OS information+
    os = platform.system()  

    if (os == 'Linux'):
        import distro   #should automatically be included on python running on linux
        linux_info = distro.linux_distribution()    # get a tuple of information about the linux distro
        os = linux_info[0] + " " + linux_info[1] + " " + linux_info[2]

    elif (os == 'Windows'):
        os = os + " " + platform.release() + " v" + platform.version()

    elif(os == 'Darwin'):
        os = "TODO, IMPLEMENT MacOS"    #TODO, implement MacOS
    
    return os

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #    


def init_connection():
    pass

def send_update():
    pass

def main():
    # Init (relatively) static variables
    hostname = socket.gethostname()     # Hostname
    os = getOS()                        # Operating System
    ram_total = 0                       # Total available RAM

    # Dynamic variables
    uptime = psutil.boot_time()                 # Uptime
    cpu_usage = psutil.cpu_percent()            # CPU Usage %
    ram_usage = psutil.virtual_memory().percent # RAM Usage %

    #processes = 0                              # Number of running processes
    #users_logged_in = 0                        # Number of users logged in




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
