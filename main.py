
#  ███████╗ █████╗ ███╗   ██╗ ██████╗ ██╗  ██╗██╗  ██╗
#  ██╔════╝██╔══██╗████╗  ██║██╔════╝ ╚██╗██╔╝╚██╗██╔╝
#  █████╗  ███████║██╔██╗ ██║██║  ███╗ ╚███╔╝  ╚███╔╝ 
#  ██╔══╝  ██╔══██║██║╚██╗██║██║   ██║ ██╔██╗  ██╔██╗ 
#  ██║     ██║  ██║██║ ╚████║╚██████╔╝██╔╝ ██╗██╔╝ ██╗
#  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
#       虽然代码写的稀烂，但是还是发出来记录一下吧！

import usb.core
import usb.util
import win32api
import win32con
import numpy as np
from multiprocessing import Process, Value, Array
import multiprocessing
import time
import os
import configparser

#平滑算法
class SavGol(object):
    def __init__(self, rank=2):
        assert window_size % 2 == 1     #注意传入数据必须除二余一
        self.window_size = window_size
        self.rank = rank
 
        self.size = int((self.window_size - 1) / 2)
        self.mm = self.create_matrix(self.size)
        self.data_seq = []
 
    def create_matrix(self, size):
        line_seq = np.linspace(-size, size, 2*size+1)
        rank_seqs = [line_seq**j for j in range(self.rank)]
        rank_seqs = np.mat(rank_seqs)
        kernel = (rank_seqs.T * (rank_seqs * rank_seqs.T).I) * rank_seqs
        mm = kernel[self.size].T
        return mm
 
    def update(self, data):
        self.data_seq.append(data)
        if len(self.data_seq) > self.window_size:
            del self.data_seq[0]
        padded_data = self.data_seq.copy()
        if len(padded_data) < self.window_size:
            left = int((self.window_size-len(padded_data))/2)
            right = self.window_size-len(padded_data)-left
            for i in range(left):
                padded_data.insert(0, padded_data[0])
            for i in range(right):
                padded_data.insert(
                    len(padded_data), padded_data[len(padded_data)-1])
        return (np.mat(padded_data)*self.mm).item()

#USB数据监听
def pause_ctrl(pctr, raww):
    print("Run pause_ctrl")
    dev = usb.core.find(idVendor=0x0483, idProduct=0x6003)      #VID,PID可根据你的设备自行更改
    if dev is None:
        raise ValueError('Device is not found')
    # 未找到设备
    dev.set_configuration()
    js = 0
    while True:
        raw = dev.read(0x81,64)     #我的板子传入数据为64字节
        ctrl = int(''.join([str(zz) for zz in raw[1:2]]))       #截取离板数据
        raw = list(np.array(raw).flatten())     #转换一维数组
        raww[:] = raw       #传出RAW数据共享变量

        #检测是否离开板子
        if ctrl == 39:      #这个判断是因为板子会每隔一段时间发送66数据
            js = js + 1
        elif ctrl == 66:
            js = 0
        pctr.value = js     #传出离板数据共享变量

#鼠标映射
def mouse_move():
    print("Run MouseMove")
    sg_x, sg_y = SavGol(), SavGol()     #实例化平滑算法
    zzz = 0
    while True:
        #动态配置重载
        dir = os.getcwd() 
        cfg = dir + "\\config.ini"
        config = configparser.ConfigParser()
        config.read(cfg,encoding='utf-8')
        XProportion = float(config['DEFAULT']['XProportion'])
        YProportion = float(config['DEFAULT']['YProportion'])
        XDisplacement = float(config['DEFAULT']['XDisplacement'])
        YDisplacement = float(config['DEFAULT']['YDisplacement'])
        SmoothCtrl = str(config['DEFAULT']['SmoothCtrl'])
        global window_size
        window_size = int(config['DEFAULT']['Smoothness'])

        #鼠标映射主循环
        while True:
            #截取数据
            raw = raww[:]
            traw = (raw[13:14])
            yaraw = (raw[9:10])
            ybraw = (raw[8:9])
            xaraw = (raw[7:8])
            xbraw = (raw[6:7])

            #处理数据
            xa = float(''.join([str(zz) for zz in xaraw]))
            xb = float(''.join([str(zz) for zz in xbraw]))
            ya = float(''.join([str(zz) for zz in yaraw]))
            yb = float(''.join([str(zz) for zz in ybraw]))
            t = int(''.join([str(zz) for zz in traw]))

            #笔左键是否按下
            if t == 17 and zzz == 0:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                zzz = 1
            if t == 16 and zzz == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                zzz = 0

            #根据配置文件调整映射位置
            xx=((xa*256+xb)/XProportion)-XDisplacement
            yy=((ya*256+yb)/YProportion)-YDisplacement

            #根据配置决定是否选用平滑算法
            if SmoothCtrl == "True" or SmoothCtrl == "true" or SmoothCtrl == "1":
                x, y = sg_x.update(xx), sg_y.update(yy)
            else:
                x, y = xx, yy
            
            #print(x, "/", y, "/", t, "/", pctr.value)
            #print(raw)

            #映射坐标
            win32api.SetCursorPos((int(x),int(y)))   

            #笔离开板子退出主循环
            if pctr.value >= 2:
                print("Pause!")
                break


        while True:
            #笔回到板子重新进入主循环
            if pctr.value == 0:
                print("Continue!")
                break


if __name__ == '__main__':
    #初始化多进程
    multiprocessing.freeze_support()

    #读配置文件
    dir = os.getcwd() 
    cfg = dir + "\\config.ini"
    config = configparser.ConfigParser()
    config.read(cfg,encoding='utf-8')
    XProportion = float(config['DEFAULT']['XProportion'])
    YProportion = float(config['DEFAULT']['YProportion'])
    XDisplacement = float(config['DEFAULT']['XDisplacement'])
    YDisplacement = float(config['DEFAULT']['YDisplacement'])
    global window_size
    window_size = int(config['DEFAULT']['Smoothness'])

    #判断USB是否已初始化
    dev = usb.core.find(idVendor=0x0483, idProduct=0x6003)
    boot = [0xAA, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    dev.write(1, boot)
    read = dev.read(0x81,64)
    read = list(np.array(read).flatten())
    read = int(''.join([str(zz) for zz in (read[4:5])]))
    '''
    print("If Not Open The Dev Please Run It Manual!")
    if read is 0:
        #打开官方程序初始化连接
        dir = dir + "\\dev\\swbdev.exe"
        dir = "start" + " " + dir
        print(dir)
        os.system(dir)

        #杀死官方程序
        time.sleep(4)
        os.system("wmic process where name='swbdev.exe'  delete")
    '''
    #初始化进程间变量共享
    raww = Array("i", 64)
    pctr = Value("i", 0)

    #实例化并启动第二进程
    cw = Process(target=pause_ctrl, args=(pctr, raww))
    cw.start()

    #启动鼠标映射函数
    mouse_move()

    