import nmap
import socket
import os
import time
import sys
import threading
from socket import gethostbyname, gethostname
from scapy.all import srp, Ether, ARP
import platform

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.sendto('Client broadcast message!', ( < broadcast > , 1060))


name = gethostname()
host = gethostbyname(name)

os.system('arp -a > temp.txt')

with open('temp.txt') as fp:
    for line in fp:
        line = line.split()[:2]

        if line and line[0].startswith(host[:4]) and (not line[0].endswith('255')):
            print(':'.join(line))

print(name)
print(host)


def get_os():
    os = platform.system()
    if os == "Windows":
        return "n"
    else:
        return "c"


def ping_ip(ip_str):
    cmd = ["ping", "-{op}".format(op=get_os()),
           "1", ip_str]
    output = os.popen(" ".join(cmd)).readlines()
    print(output)
    flag = False
    for line in list(output):
        if not line:
            continue
        if str(line).upper().find("TTL") >= 0:
            flag = True
            break
    if flag:
        print(ip_str)


def find_ip(ip_prefix):
    for i in range(1, 256):
        ip = '%s.%s' % (ip_prefix, i)
        t = threading.Thread(target=ping_ip, args=(ip,))
        # t.setDaemon(True)
        t.start()


if __name__ == "__main__":
    args = "192.168.10.1"
    ip_prefix = '.'.join(args.split('.')[:-1])
    find_ip(ip_prefix)
