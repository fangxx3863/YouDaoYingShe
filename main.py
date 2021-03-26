import usb.core
import usb.util
import win32gui
import win32api
import win32con
import sys
from pynput.keyboard import Key, Listener
from multiprocessing import Process, Value
import pynput.keyboard
import pynput
import multiprocessing
import time
import os
import configparser
#import multiprocessing_win



def keyboard_listener(q):
    print("Run KeyListener")
    def on_release(key):  # 按键被松开调用这个函数
        q.value = 0
        if key == Key.pause:
            q.value = 2
            time.sleep(1)
            q.value = 0
        if key == Key.f4:  # 如果按了F4键就停止监听
            q.value = 1
            return False  # Stop listener
    # 连接事件以及释放
    with Listener(on_release=on_release) as listener:
        listener.join()

def mouse_move():
    print("Run MouseMove")
    dev = usb.core.find(idVendor=0x0483, idProduct=0x6003)
    if dev is None:
        raise ValueError('Device is not found')
    # device is found :-)
    dev.set_configuration()
    zzz = 0
    dot="."
    while True:
        while True:
            raw = dev.read(0x81,1000)
            traw = (raw[13:14])
            yaraw = (raw[9:10])
            ybraw = (raw[8:9])
            xaraw = (raw[7:8])
            xbraw = (raw[6:7])
            xa = float(''.join([str(zz) for zz in xaraw]))
            xb = float(''.join([str(zz) for zz in xbraw]))
            ya = float(''.join([str(zz) for zz in yaraw]))
            yb = float(''.join([str(zz) for zz in ybraw]))
            t = int(''.join([str(zz) for zz in traw]))

            if t == 17 and zzz == 0:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                zzz = 1
            if t == 16 and zzz == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                zzz = 0

            xx=((xa*256+xb)/XProportion)-XDisplacement               #在这里修改映射大小及位移
            yy=((ya*256+yb)/YProportion)-YDisplacement               #在这里修改映射大小及位移
            xx=int(str(xx).split('.')[0] )
            yy=int(str(yy).split('.')[0] )
            #print(xx,"/",yy,"/",t)
            win32api.SetCursorPos((xx,yy))   
            
            if q.value == 1:
                print("Exit!")
                sys.exit()
            if q.value == 2:
                print("Pause!")
                q.value = 0
                break

        while True:
            if q.value == 2:
                q.value = 0
                print("Continue!")
                break


if __name__ == '__main__':
    multiprocessing.freeze_support()
    dir = os.getcwd() 
    cfg = dir + "\\config.ini"
    config = configparser.ConfigParser()
    config.read(cfg,encoding='utf-8')
    XProportion = float(config['DEFAULT']['XProportion'])
    YProportion = float(config['DEFAULT']['YProportion'])
    XDisplacement = float(config['DEFAULT']['XDisplacement'])
    YDisplacement = float(config['DEFAULT']['YDisplacement'])
    dir = dir + "\\dev\\swbdev.exe"
    dir = "start" + " " + dir
    print(dir)
    os.system(dir)
    time.sleep(4)
    os.system("wmic process where name='swbdev.exe'  delete")

    q=Value("d",10.0)
    pw=Process(target=keyboard_listener, args=(q,))
    pw.start()
    mouse_move()

    
