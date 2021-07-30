import usb.core
import usb.util
import win32gui
import win32api
import win32con
import sys
import numpy as np
#from pynput.keyboard import Key, Listener
from multiprocessing import Process, Value, Array
#import pynput.keyboard
#import pynput
import multiprocessing
import time
import os
import configparser
#import multiprocessing_win


def pause_ctrl(pctr, raww):
    print("Run pause_ctrl")
    dev = usb.core.find(idVendor=0x0483, idProduct=0x6003)
    if dev is None:
        raise ValueError('Device is not found')
    # device is found :-)
    dev.set_configuration()
    #zzz = 0
    js = 0
    while True:
        raw = dev.read(0x81,64)
        ctrl = int(''.join([str(zz) for zz in raw[1:2]]))
        raww[:] = list(np.array(raw).flatten())
        #print(raww)
        if ctrl == 39:
            js = js + 1
        elif ctrl == 66:
            js = 0
        pctr.value = js





def mouse_move():
    print("Run MouseMove")
    #dev = usb.core.find(idVendor=0x0483, idProduct=0x6003)
    #if dev is None:
    #    raise ValueError('Device is not found')
    # device is found :-)
    #dev.set_configuration()
    zzz = 0
    while True:
        dir = os.getcwd() 
        cfg = dir + "\\config.ini"
        config = configparser.ConfigParser()
        config.read(cfg,encoding='utf-8')
        XProportion = float(config['DEFAULT']['XProportion'])
        YProportion = float(config['DEFAULT']['YProportion'])
        XDisplacement = float(config['DEFAULT']['XDisplacement'])
        YDisplacement = float(config['DEFAULT']['YDisplacement'])
        while True:
            #raw = dev.read(0x81,1000)
            raw = raww[:]
            traw = (raw[13:14])
            yaraw = (raw[9:10])
            ybraw = (raw[8:9])
            xaraw = (raw[7:8])
            xbraw = (raw[6:7])
            #ctrl = int(''.join([str(zz) for zz in raw[1:2]]))
            #print(raw)
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
            #xx=int(str(xx).split('.')[0] )
            #yy=int(str(yy).split('.')[0] )
            xx=int(xx)
            yy=int(yy)
            print(xx, "/", yy, "/", t, "/", pctr.value)
            #print(raw)
            #print(raw)
            win32api.SetCursorPos((xx,yy))   

            if pctr.value >= 2:
                print("Pause!")
                break

        while True:
            if pctr.value == 0:
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

    raww = Array("i", 64)
    pctr = Value("i")
    cw = Process(target=pause_ctrl, args=(pctr, raww))
    cw.start()
    mouse_move()

    
