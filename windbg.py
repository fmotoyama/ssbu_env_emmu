# -*- coding: utf-8 -*-
"""
Created on Wed May 18 08:33:50 2022

@author: f.motoyama
"""

import subprocess, re, array
import pandas as pd
import ctypes, win32gui

#import os, sys
#sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import defines as d


########## VirtualQueryEx関連 ##########
PAGE_NOACCESS          = 0x01
PAGE_READONLY          = 0x02
PAGE_READWRITE         = 0x04
PAGE_WRITECOPY         = 0x08
PAGE_EXECUTE           = 0x10
PAGE_EXECUTE_READ      = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80
PAGE_GUARD            = 0x100
PAGE_NOCACHE          = 0x200
PAGE_WRITECOMBINE     = 0x400
MEM_COMMIT           = 0x1000
MEM_RESERVE          = 0x2000
MEM_DECOMMIT         = 0x4000
MEM_RELEASE          = 0x8000
MEM_FREE            = 0x10000
MEM_PRIVATE         = 0x20000
MEM_MAPPED          = 0x40000
MEM_RESET           = 0x80000
MEM_TOP_DOWN       = 0x100000
MEM_WRITE_WATCH    = 0x200000
MEM_PHYSICAL       = 0x400000
MEM_RESET_UNDO    = 0x1000000
MEM_LARGE_PAGES  = 0x20000000
MEM_4MB_PAGES    = 0x80000000
SEC_FILE           = 0x800000
SEC_IMAGE         = 0x1000000
SEC_RESERVE       = 0x4000000
SEC_COMMIT        = 0x8000000
SEC_NOCACHE      = 0x10000000
SEC_LARGE_PAGES  = 0x80000000
MEM_IMAGE         = SEC_IMAGE
WRITE_WATCH_FLAG_RESET = 0x01
FILE_MAP_ALL_ACCESS = 0xF001F


class MemoryBasicInformation (object):
    """
    Memory information object returned by L{VirtualQueryEx}.
    """
    READABLE = (
                PAGE_EXECUTE_READ       |
                PAGE_EXECUTE_READWRITE  |
                PAGE_EXECUTE_WRITECOPY  |
                PAGE_READONLY           |
                PAGE_READWRITE          |
                PAGE_WRITECOPY
    )

    WRITEABLE = (
                PAGE_EXECUTE_READWRITE  |
                PAGE_EXECUTE_WRITECOPY  |
                PAGE_READWRITE          |
                PAGE_WRITECOPY
    )

    COPY_ON_WRITE = (
                PAGE_EXECUTE_WRITECOPY  |
                PAGE_WRITECOPY
    )

    EXECUTABLE = (
                PAGE_EXECUTE            |
                PAGE_EXECUTE_READ       |
                PAGE_EXECUTE_READWRITE  |
                PAGE_EXECUTE_WRITECOPY
    )

    EXECUTABLE_AND_WRITEABLE = (
                PAGE_EXECUTE_READWRITE  |
                PAGE_EXECUTE_WRITECOPY
    )

    def __init__(self, mbi=None):
        """
        @type  mbi: L{MEMORY_BASIC_INFORMATION} or L{MemoryBasicInformation}
        @param mbi: Either a L{MEMORY_BASIC_INFORMATION} structure or another
            L{MemoryBasicInformation} instance.
        """
        if mbi is None:
            self.BaseAddress        = None
            self.AllocationBase     = None
            self.AllocationProtect  = None
            self.RegionSize         = None
            self.State              = None
            self.Protect            = None
            self.Type               = None
        else:
            self.BaseAddress        = mbi.BaseAddress
            self.AllocationBase     = mbi.AllocationBase
            self.AllocationProtect  = mbi.AllocationProtect
            self.RegionSize         = mbi.RegionSize
            self.State              = mbi.State
            self.Protect            = mbi.Protect
            self.Type               = mbi.Type

            # Only used when copying MemoryBasicInformation objects, instead of
            # instancing them from a MEMORY_BASIC_INFORMATION structure.
            if hasattr(mbi, 'content'):
                self.content = mbi.content
            if hasattr(mbi, 'filename'):
                self.content = mbi.filename

    def __contains__(self, address):
        """
        Test if the given memory address falls within this memory region.
        @type  address: int
        @param address: Memory address to test.
        @rtype:  bool
        @return: C{True} if the given memory address falls within this memory
            region, C{False} otherwise.
        """
        return self.BaseAddress <= address < (self.BaseAddress + self.RegionSize)

    def is_free(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region is free.
        """
        return self.State == MEM_FREE

    def is_reserved(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region is reserved.
        """
        return self.State == MEM_RESERVE

    def is_commited(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region is commited.
        """
        return self.State == MEM_COMMIT

    def is_image(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region belongs to an executable
            image.
        """
        return self.Type == MEM_IMAGE

    def is_mapped(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region belongs to a mapped file.
        """
        return self.Type == MEM_MAPPED

    def is_private(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region is private.
        """
        return self.Type == MEM_PRIVATE

    def is_guard(self):
        """
        @rtype:  bool
        @return: C{True} if all pages in this region are guard pages.
        """
        return self.is_commited() and bool(self.Protect & PAGE_GUARD)

    def has_content(self):
        """
        @rtype:  bool
        @return: C{True} if the memory in this region has any data in it.
        """
        return self.is_commited() and not bool(self.Protect & (PAGE_GUARD | PAGE_NOACCESS))

    def is_readable(self):
        """
        @rtype:  bool
        @return: C{True} if all pages in this region are readable.
        """
        return self.has_content() and bool(self.Protect & self.READABLE)

    def is_writeable(self):
        """
        @rtype:  bool
        @return: C{True} if all pages in this region are writeable.
        """
        return self.has_content() and bool(self.Protect & self.WRITEABLE)

    def is_copy_on_write(self):
        """
        @rtype:  bool
        @return: C{True} if all pages in this region are marked as
            copy-on-write. This means the pages are writeable, but changes
            are not propagated to disk.
        @note:
            Typically data sections in executable images are marked like this.
        """
        return self.has_content() and bool(self.Protect & self.COPY_ON_WRITE)

    def is_executable(self):
        """
        @rtype:  bool
        @return: C{True} if all pages in this region are executable.
        @note: Executable pages are always readable.
        """
        return self.has_content() and bool(self.Protect & self.EXECUTABLE)

    def is_executable_and_writeable(self):
        """
        @rtype:  bool
        @return: C{True} if all pages in this region are executable and
            writeable.
        @note: The presence of such pages make memory corruption
            vulnerabilities much easier to exploit.
        """
        return self.has_content() and bool(self.Protect & self.EXECUTABLE_AND_WRITEABLE)


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BaseAddress',         d.SIZE_T),    # remote pointer
        ('AllocationBase',      d.SIZE_T),    # remote pointer
        ('AllocationProtect',   d.DWORD),
        ('RegionSize',          d.SIZE_T),
        ('State',               d.DWORD),
        ('Protect',             d.DWORD),
        ('Type',                d.DWORD),
    ]

PMEMORY_BASIC_INFORMATION = d.POINTER(MEMORY_BASIC_INFORMATION)


def VirtualQueryEx(hProcess, lpAddress):
    _VirtualQueryEx = ctypes.windll.kernel32.VirtualQueryEx
    _VirtualQueryEx.argtypes = [d.HANDLE, d.LPVOID, PMEMORY_BASIC_INFORMATION, d.SIZE_T]
    _VirtualQueryEx.restype  = d.SIZE_T

    lpBuffer  = MEMORY_BASIC_INFORMATION()
    dwLength  = ctypes.sizeof(MEMORY_BASIC_INFORMATION)
    success   = _VirtualQueryEx(hProcess, lpAddress, ctypes.byref(lpBuffer), dwLength)
    if success == 0:
        raise ctypes.WinError()
    return MemoryBasicInformation(lpBuffer)


def get_memorymap(pHandle):
    data = []
    offset = 0
    item = list(MemoryBasicInformation().__dict__.keys())
    try:
        while True:
            temp = VirtualQueryEx(pHandle, offset)
            data.append(temp.__dict__.values())
            offset = temp.BaseAddress + temp.RegionSize
    except OSError:
        pass
    
    df = pd.DataFrame(data, columns=item)
    return df



########## その他 ##########
def get_all_process():
    """実行中のプロセスの情報をまとめる"""
    proc = subprocess.Popen('tasklist', shell=True, stdout=subprocess.PIPE)
    
    data = list(proc.stdout)
    item = data[1].decode("sjis").split()
    item[-1] += '(K)'
    match = list(re.finditer(r'.*?(=+)', data[2].decode("utf-8"))) #'='の集合の検索
    boundary = [[m.start(),m.end()] for m in match]
    plist = []
    for line in data[3:]:
        line = line.decode("utf-8")
        temp = [line[b[0]:b[1]] for b in boundary]
        temp[4] = re.match('.*?(\d+)', temp[4]).group()     #数字の検索（Kの削除）
        plist.append(temp)
    
    df = pd.DataFrame(plist,columns=item)
    df = df.astype({'PID': 'int32', 'セッション#': 'int8', 'メモリ使用量(K)': 'int32'})
    df['イメージ名'] = df['イメージ名'].str.strip(); df['セッション名'] = df['セッション名'].str.strip()
    return df


def get_pids(name):
    """nameのPIDを全て返す"""
    df = get_all_process()
    df2 = df[df['イメージ名'] == name]
    
    if len(df2) == 0:
        print(f'not found "{name}" PID')
        return
    return df2['PID'].tolist()


def get_pHandle(pid):
    """pidのプロセスハンドルを取得"""
    PROCESS_ALL_ACCESS = 0x001F0FFF
    pHandles = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    return pHandles


def close_pHandle(pHandle):
    """プロセスハンドルを全て閉じる"""
    if not ctypes.windll.kernel32.CloseHandle(pHandle):
        print(ctypes.WinError(ctypes.GetLastError()))


ReadProcessMemory = ctypes.windll.kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = (ctypes.c_ushort, ctypes.c_ulonglong, ctypes.c_char_p, ctypes.c_ushort, ctypes.c_void_p)
ReadProcessMemory.restypes = None
def peek(pHandle, address, size):
    """仮想メモリのaddressの値を取得　0xffffより大きいsizeは読めない"""
    buf = ctypes.create_string_buffer(size)
    if ReadProcessMemory(pHandle, address, buf, size, None):
        return(buf.raw)
    else:
        print(f'faild to peek {hex(address)}')
        return None



def EnumWindows():
    """すべてのウィンドウについて[ウィンドウ名,wHandle,pid]を求める"""
    user32 = ctypes.WinDLL("user32")
    #コールバック関数
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    #トップレベルウィンドウのハンドルを順番にコールバック関数へ送る
    user32.EnumWindows.restype = ctypes.c_bool
    user32.EnumWindows.argtypes = (EnumWindowsProc, ctypes.c_void_p)
    #ウィンドウタイトルをバッファにコピー
    user32.GetWindowTextW.restype = ctypes.c_int32
    user32.GetWindowTextW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int32)
    #ウィンドウを作成したtidを返す ポインタが与えられていればそこにpidをコピー
    user32.GetWindowThreadProcessId.restype = ctypes.c_uint32
    
    window_info_all = []    #[ウィンドウ名,wHandle,pid]
    def callback(hwnd, lParam):
        #ウィンドウタイトルの取得
        l = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(l + 1)
        user32.GetWindowTextW(hwnd, buff, l + 1)
        #pidの取得
        ptr = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(ptr))    # = tid
        
        window_info_all.append([buff.value, hwnd, ptr.value])
        return True
    
    user32.EnumWindows(EnumWindowsProc(callback), None)
    return(window_info_all)


def EnumChildWindows(wHandle):
    """wHandleの子ウィンドウのハンドルを取得"""
    #ENUM_CHILD_WINDOWS = ctypes.WINFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.py_object)
    wcHandles = array.array('i')
    win32gui.EnumChildWindows(
        wHandle,
        lambda handle,list:list.append(handle),
        wcHandles
        )
    """
    data = {}
    for wcHandle in wcHandles:
        c_class_name = win32gui.GetClassName(wcHandle)
        c_handle_name = win32gui.GetWindowText(wcHandle)
        #print('c',hex(wcHandle),c_class_name,c_handle_name)
        data[str(wcHandle)] = [c_class_name,c_handle_name]
    """
    return(wcHandles.tolist())


def SetWindowText(wHandle,text):
    win32gui.SetWindowText(wHandle,text)


if __name__ == "__main__":
    pids = get_pids('yuzu.exe')
    pHandles = [get_pHandle(pid) for pid in pids]
    
    df = get_memorymap(pHandles[0])
    df2 = df[df['RegionSize'] == 0x1_00000000]
    
    infos_all = EnumWindows()
    infos = [info for info in infos_all if 'yuzu' in info[0]]
    
    #wHandleからpHandleを取得
    #親・子ウィンドウハンドルでpHandlesと値があわない
    #pHandles2 = [ctypes.windll.oleacc.GetProcessHandleFromHwnd(info[1]) for info in infos]
    
    SetWindowText(infos[3][1], infos[3][0] + '_0')


