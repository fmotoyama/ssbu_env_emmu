# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 14:49:23 2021

@author: f.motoyama
"""
import struct

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import windbg, config


class ReadMemory:
    def __init__(self, pHandle):
        self.pHandle = pHandle
        #heapfreeを取得
        mmap = windbg.get_memorymap(pHandle)
        df = mmap[mmap['RegionSize'] == 0x1_00000000]
        assert len(df) == 1, f"heapfreeのページを特定できませんでした len(mmap[mmap['RegionSize'] == 0x1_00000000])={len(df)}"
        self.a_free = int(df['BaseAddress']) + config.ra_free
        #print(hex(self.a_free))
    
    def peek_collected_param(self):
        l = len(config.chains)
        data = windbg.peek(self.pHandle, self.a_free, l * 4)
        R = {name:self.bytes2type(data[i*4:i*4+4], _type) for i,(name,_type) in enumerate(config.chains.items())}
        return R
    
    @staticmethod
    def bytes2type(_bytes, _type):
        if _type == 'float':
            return struct.unpack('<f', _bytes)[0]
        elif _type == 'int':
            return int.from_bytes(_bytes, 'little')
        elif _type == 'bytes':
            return _bytes
        elif _type == 'hex':
            return _bytes.hex()

    def __del__(self):
        windbg.close_pHandle(self.pHandle)
    



if __name__ == '__main__':
    pids = windbg.get_pids('yuzu.exe')
    pHandles = [windbg.get_pHandle(pid) for pid in pids]
    
    pHandle = pHandles[0]
    read_memory = ReadMemory(pHandle)
    
    a_free = hex(read_memory.a_free)
    #sign = [bytes2type(windbg.peek(pHandles[i], heapfrees[i], 4), 'hex') for i in range(len(pHandles))]
    param = read_memory.peek_collected_param()
    
    data = []
    frame1 = param['frame']
    while True:
        temp = read_memory.peek_collected_param()
        if temp['frame'] != frame1:
            data.append([temp['frame'],temp['posx1']])
        if temp['frame'] - frame1 == 2:
            break
    



    
    
    
    
    
    
    
    
    
