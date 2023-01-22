# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 13:52:55 2021

@author: f.motoyama
"""
import ctypes

BOOL        = ctypes.c_bool     #2022/04/20
WORD        = ctypes.c_uint16   #2022/04/20
DWORD       = ctypes.c_uint32
LONG        = ctypes.c_long
LONGLONG    = ctypes.c_longlong
LPVOID      = ctypes.c_void_p
BYTE        = ctypes.c_ubyte
TCHAR       = ctypes.c_char


SIZE_T      = ctypes.c_size_t

POINTER     = ctypes.POINTER
ULONG_PTR   = SIZE_T

HANDLE      = LPVOID
HMODULE     = HANDLE





ERROR_NO_MORE_FILES     = 18



