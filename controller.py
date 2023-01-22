# -*- coding: utf-8 -*-
"""
Created on Sat May 21 19:32:52 2022

@author: f.motoyama
"""
import win32api, win32con
import time

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import windbg

class KeyValue:
    N       = 0,
    #Button
    A       = ord('C')  #通常攻撃（ホールドあり）
    B       = ord('X')  #必殺攻撃
    X       = ord('V')  #ジャンプ1
    Y       = ord('Z')  #ジャンプ2
    R       = ord('R')  #ガード（ホールドあり）
    ZL      = ord('Q')  #つかみ1
    ZR      = ord('E')  #つかみ2
    PLUS    = ord('M')
    #Stick
    right   = ord('D')
    up      = ord('W')
    left    = ord('A')
    down    = ord('S')
    shift   = 0x10
        


class Controller:

    PostMessage = win32api.PostMessage
    WM_KEYDOWN = win32con.WM_KEYDOWN
    WM_KEYUP = win32con.WM_KEYUP
    
    def __init__(self,wHandle):
        self.wHandle = wHandle
        self.button_pre = []       #現在押下状態のボタン
        self.stick_pre = []
    
    def keyPress(self, value):
        Controller.PostMessage(self.wHandle, Controller.WM_KEYDOWN, value, 0)
    
    def keyRelease(self, value):
        Controller.PostMessage(self.wHandle, Controller.WM_KEYUP, value, 0)
    
    def keyClick(self, value, wait = 2/60):
        self.keyPress(value)
        time.sleep(2/60)
        self.keyRelease(value)
        time.sleep(wait)
    
    def set_neutral(self):
        keys = [v for v in vars(KeyValue).values() if type(v) is int]
        for key in keys:
            self.keyRelease(key)
    
    def TrainingMode_reset(self):
        values = [KeyValue.A, KeyValue.ZL, KeyValue.ZR]
        for value in values:
            self.keyPress(value)
        time.sleep(2/60)
        for value in values:
            self.keyRelease(value)
    
    def TrainingMode_enemy_activate(self):
        self.keyClick(KeyValue.PLUS, 0.5)
        for _ in range(4):
            self.keyClick(KeyValue.down, 0.3)
        self.keyClick(KeyValue.right, 0.3)
        self.keyClick(KeyValue.PLUS)
    
    def TrainingMode_enemy_deactivate(self):
        self.keyClick(KeyValue.PLUS, 0.5)
        self.keyClick(KeyValue.left, 0.3)
        for _ in range(4):
            self.keyClick(KeyValue.up, 0.3)
        self.keyClick(KeyValue.PLUS)
        
    
    def __del__(self):
        self.set_neutral()
        
    
    


if __name__ == "__main__":
    
    infos_all = windbg.EnumWindows()  
    infos = [info for info in infos_all if info[0][:5] == 'yuzu ']
    wcHandles = windbg.EnumChildWindows(infos[0][1])
    #wcHandle = wcHandles[3]
    wcHandle = wcHandles[4]
    
    c = Controller(wcHandle)
    #弱
    #c.keyClick(KeyValue.A)
    #横強上シフト
    c.keyPress(KeyValue.B)
    #c.keyPress(KeyValue.shift)
    c.keyPress(KeyValue.right)
    #c.keyPress(KeyValue.up)
    time.sleep(0.5)
    c.set_neutral()
    time.sleep(0.5)
    
    c.TrainingMode_reset()
    
    
    
    
    """
    #temp = win32api.PostMessage(wcHandles[3], win32con.WM_KEYDOWN, win32con.VK_SPACE, 0)
    #temp = win32api.PostMessage(wcHandles[3], win32con.WM_KEYUP, 0x43, 0)
    temp = win32api.PostMessage(wcHandles[3], 0x0100, 0x43, 0)
    time.sleep(0.1)
    temp = win32api.PostMessage(wcHandles[3], 0x0101, 0x43, 0)
    time.sleep(0.1)
    temp = win32api.PostMessage(wcHandles[3], 0x0100, 0x58, 0)
    time.sleep(0.1)
    temp = win32api.PostMessage(wcHandles[3], 0x0101, 0x58, 0)
    """
    

