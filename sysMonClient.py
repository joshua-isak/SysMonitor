import socket
import time
import psutil

import platform



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

def getUptime(): # Get system uptime and return a tuple (days, hours, minutes)
    seconds = time.time() - psutil.boot_time()
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    day, hour = divmod(hour, 24)
    
    return day, hour, min

def init_connection():
    pass

def send_update():
    pass

def main():
    # init (relatively) static variables
    hostname = socket.gethostname()     # Hostname
    os = getOS()
    uptime = getUptime() #TODO when not testing just get psutil.boot_time() and convert on the phone-home server


    # Test out variables
    print("Hostname: " + hostname )
    print("OS: " + os)
    print("Uptime: " + str(uptime))

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
