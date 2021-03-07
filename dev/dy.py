import os
import time

dir = os.getcwd() 
dir = dir + "\\dev\\swbdev.exe"
dir = "start" + " " + dir
print(dir)
os.system(dir)
time.sleep(4)
os.system("wmic process where name='swbdev.exe'  delete")