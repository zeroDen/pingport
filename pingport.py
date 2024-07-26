import socket
import time
import sys
import win32api
import keyboard
from colorama import init, Fore, Style
import ctypes
import subprocess
import re
from requests import get
import maxminddb
import random
import requests
import os

# 185.15.59.224 wikipedia.org
host_to_ping = 'speedtest.selectel.ru'

def test_download_speed(url):
    anti_cache_stamp = random.randint(0, 0xFFFFFFFF)
    url = url + '?x=%s' % anti_cache_stamp

    start_time = time.time()
    response = requests.get(url, stream=True)
    total_length = response.headers.get('content-length')

    if total_length is None:
        data = response.content
    else:
        dl = 0
        data = bytearray()
        total_length = int(total_length)
        for chunk in response.iter_content(chunk_size=4096):
            dl += len(chunk)
            data.extend(chunk)

    end_time = time.time()
    elapsed_time = end_time - start_time

    down_speed_byte = round(len(data) / elapsed_time, 2)  # Calculate speed based on the data length

    # Explicitly discard the accumulated data
    del data

    return down_speed_byte

def get_download_speed():
    timedate_stamp = time.strftime('%Y-%m-%d %H:%M:%S')    
    print(f'[{timedate_stamp}] testing download speed... ', end='')
    
    ping = PingHost(host_to_ping)
    print(f'ping ' + Style.BRIGHT + Fore.YELLOW + f'{ping}' + Style.RESET_ALL + ' ms; ', end='')

    speed1 = test_download_speed('https://speedtest.selectel.ru/10MB')
    speed2 = test_download_speed('http://ipv4.download.thinkbroadband.com/5MB.zip')
    speed3 = test_download_speed('http://212.183.159.230/5MB.zip')
    
    # resulting speed is max of three
    down_speed_mbyte = max([speed1, speed2, speed3])
    down_speed_mbit = down_speed_mbyte * 8
    # convert to mega
    down_speed_mbyte = round(down_speed_mbyte / 1_000_000, 1)
    down_speed_mbit = round(down_speed_mbit / 1_000_000, 1)
    speed1 = round(speed1 * 8 / 1_000_000)
    speed2 = round(speed2 * 8 / 1_000_000)
    speed3 = round(speed3 * 8 / 1_000_000)

    print('download ' + Style.BRIGHT + Fore.YELLOW + f'{down_speed_mbit}' + Style.RESET_ALL + f' mbit ({down_speed_mbyte} mbyte, {speed1}/{speed2}/{speed3});')

    speed_file = 'speed.csv'
    # if speed file not exist create header in it
    if not os.path.exists(speed_file):
        with open(speed_file, 'a') as myfile:
            myfile.write('"DATETIME","PING","DOWNLOAD"\n')
    with open(speed_file, 'a') as myfile:
        myfile.write(f'"{timedate_stamp}","{ping}","{down_speed_mbit}"\n')

def GetWinUptime(): 
    # getting the library in which GetTickCount64() resides
    lib = ctypes.windll.kernel32
     
    # calling the function and storing the return value
    t = lib.GetTickCount64()
     
    # since the time is in milliseconds i.e. 1000 * seconds
    # therefore truncating the value
    t = int(str(t)[:-3])
     
    # extracting hours, minutes, seconds & days from t
    # variable (which stores total time in seconds)
    mins, sec = divmod(t, 60)
    hour, mins = divmod(mins, 60)
    days, hour = divmod(hour, 24)
     
    # formatting the time in readable form
    # (format = x days, HH:MM:SS)
    return f"{days} days, {hour:02}:{mins:02}:{sec:02}"

def DupeConsoleToFile(filepath):
    class Logger(object):
        def __init__(self):
            self.logfile = open(filepath, 'ab', 0)
            self.prevstdout = sys.stdout

        def write(self, message):
            self.prevstdout.write(message)
            self.prevstdout.flush()
            self.logfile.write(message.encode())
            self.logfile.flush()

        def __del__(self):
            self.logfile.close()

        def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
            pass

    sys.stdout = Logger()
    # no necessary, but redirect errors too
    sys.stderr = sys.stdout

def Percentage(whole, part):
    if whole:
        perc = 100 * float(part) / float(whole)
    else:
        perc = 0
    return str(round(perc))

def custom_sleep(i):
    while i:
        if ping_fails:
            ping_fails_str = ' (fails %d)' % ping_fails
            win32api.SetConsoleTitle('pingport %d%s' % (i, ping_fails_str))
        else:
            win32api.SetConsoleTitle('pingport %d' % i)
        i = i - 1
        j = 10
        while j:
            j = j - 1
            time.sleep(0.1)
            if (keyboard.is_pressed('f1')):
                # manual ping
                print('m', end='')
                i = 0
                j = 0

def PingHost(host):
    try:
        output = subprocess.check_output(["ping", "-n", "1", host], stderr=subprocess.STDOUT, universal_newlines=True)
        # Extract the time in ms using regular expressions
        time_match = re.search(r'time[=<](\d+)', output)
        if time_match:
            time_ms = int(time_match.group(1))
            return time_ms
        else:
            return -1  # General failure
    except (subprocess.CalledProcessError, PermissionError, Exception):
        return -1  # General failure

ping_fails = 0
ping_fails_str = ''
def CustomPing(host):
    # ping using classical ping
    ret_ping = PingHost(host)
    # make second ping try
    if ret_ping < 0:
        custom_sleep(5)
        ret_ping = PingHost(host)
    if ret_ping >= 0:
        print(Style.BRIGHT + Fore.GREEN + '%d' % ret_ping, end='')
    else:
        print(Style.BRIGHT + Fore.RED + '\n' + '%s ping down %d' % (timedate_stamp, ping_fails + 1))

    # ping using connect ping
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ret_sock = sock.connect_ex((host, 80))
    if sock:
        sock.close()
    if ret_sock == 0:
        print(Style.BRIGHT + Fore.GREEN + '.', end='');
    else:
        print(Style.BRIGHT + Fore.RED + '\n' + '%s conn down %d' % (timedate_stamp, ping_fails + 1))

    # successful only if both type of pings are ok
    return ret_ping >= 0 and ret_sock == 0

def reverse_ip(ip):
    try:
        host_rev = socket.gethostbyaddr(ip)[0]
    except (socket.herror) as err:
        host_rev = err
    return host_rev

logfilename = time.strftime('%Y%m%d_%H%M%S_pingport.log')
DupeConsoleToFile(logfilename)
timedate_stamp = time.strftime('[%Y-%m-%d %H:%M:%S]')
init(convert=True, autoreset=True)
print(Style.BRIGHT + Fore.CYAN + time.strftime(timedate_stamp + ' pingport started'))
print('python version: "%s"' % sys.version)
print('python path: "%s"' % sys.executable)
print('windows uptime: "%s"' % GetWinUptime())
print('host to ping: "%s"' % host_to_ping)
host_to_ping_ip = socket.gethostbyname(host_to_ping)
print('host to ping ip: "%s"' % host_to_ping_ip)
print('host to ping reverse: "%s"' % reverse_ip(host_to_ping_ip))
loc_ip = socket.gethostbyname(socket.getfqdn())
print('local ip: "%s"' % loc_ip)
print('local ip reverse: "{}"'.format(reverse_ip(loc_ip)))
print('local name: "%s"' % socket.getfqdn())
wan_ip = get('https://api.ipify.org').content.decode('utf8')
print('wan ip: "{}"'.format(wan_ip))
print('wan ip reverse: "{}"'.format(reverse_ip(wan_ip)))
with maxminddb.open_database('dbip-asn-lite-2024-07.mmdb') as reader:
    rec = reader.get(wan_ip)
    print('isp: "%s"' % rec['autonomous_system_organization'])

get_download_speed()

print("Press F1 for a manual ping")

timemark_prev_hour = time.time()
ping_hour_attempts = 0
ping_day_attempts = 0
ping_hour_ok = 0
ping_day_ok = 0
hour_count = 0
day_count = 0
day_stat_reset = 1

while True:
    time_stamp = time.strftime('%H:%M:%S')
    timedate_stamp = time.strftime('[%Y-%m-%d %H:%M:%S]')
    timemark_now = time.time()

    # print hour stat
    hour_timediff = (timemark_now - timemark_prev_hour) / 3600
    if (hour_timediff >= 1):
        # reset hour marker
        timemark_prev_hour = timemark_now
        perc = Percentage(ping_hour_attempts, ping_hour_ok)
        # if computer slept for some time print how many hours
        if (hour_timediff >= 2):
            print(Style.BRIGHT + '\n' + timedate_stamp + ' +%d hours' % hour_timediff)
        # print regular hour mark
        else:
            hour_count += 1
            partial = ''
            if ping_hour_attempts != ping_hour_ok:
                partial = ' partial'
            print('\n' + timedate_stamp + ' hour%02d%s uptime %s%%, %d outof %d %s' % (hour_count, partial, perc, ping_hour_ok, ping_hour_attempts, ping_fails_str))
        # reset hour counters
        ping_hour_attempts = 0
        ping_hour_ok = 0
        get_download_speed()

    # print day stat
    if (day_stat_reset and hour_count != 0 and hour_count % 24 == 0):
        day_stat_reset = 0
        perc = Percentage(ping_day_attempts, ping_day_ok)
        day_count += 1
        partial = ''
        if ping_day_attempts != ping_day_ok:
            partial = ' partial'
        print(Style.BRIGHT + timedate_stamp + ' day%d  %s uptime %s%%, %d outof %d %s' % (day_count, partial, perc, ping_day_ok, ping_day_attempts, ping_fails_str))
        print('windows uptime: "%s"' % GetWinUptime())
        # reset day counters
        ping_day_attempts = 0
        ping_day_ok = 0
    # reset day stat status to avoid stat dupes
    elif (hour_count != 0 and hour_count % 25 == 0):
        day_stat_reset = 1

    ping_hour_attempts += 1
    ping_day_attempts += 1

    result = CustomPing(host_to_ping)
    if result:
        ping_hour_ok += 1
        ping_day_ok += 1
    else:
        ping_fails += 1
        # don't wait long time for next try
        custom_sleep(10)
        continue

    custom_sleep(120)
