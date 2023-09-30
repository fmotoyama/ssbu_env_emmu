# -*- coding: utf-8 -*-
"""
Created on Fri Nov 11 12:44:48 2022

@author: f.motoyama
"""
import os, re
import pandas as pd

from . import windbg


def get_label(name1:str,name2:str):
    """
    ID:ラベルの辞書を得る
    同じIDでラベルが異なるとき、先のラベルが上書きされる
    Args:
        name1,2(str)
    Returns:
        dict1,2 = {motionID : label},
    """
    base = os.path.dirname(os.path.abspath(__file__))
    name = os.path.normpath(os.path.join(base, r'..\label.csv'))
    df = pd.read_csv(name, encoding="SHIFT-JIS", dtype = 'object')
    motion_variable = {}
    for name in ['0',name1,name2]:
        df_temp = df[[name, name+'label']].dropna(how='any')
        for _,ID,label in df_temp.itertuples(name=None):
            motion_variable[int(ID, 16)] = label
    return motion_variable



def get_motion_variable(name1:str,name2:str):
    """
    motion_variableの辞書を返す
    motion_variable = [button(4 dummyvariable),stick(5 dummyvariable),situation(3 dummyvariable)]
    """
    base = os.path.dirname(os.path.abspath(__file__))
    name = os.path.normpath(os.path.join(base, r'..\label.csv'))
    df = pd.read_csv(name, encoding="SHIFT-JIS", dtype = 'object')
    motion_variable = {}
    for name in ['0',name1,name2]:
        df_temp = df[[name, name+'button', name+'stick', name+'situation']].dropna(how='any')
        for _,ID,button,stick,situation in df_temp.itertuples(name=None):
            variable = [0 for _ in range(12)]
            for s in button:
                if s != '0':
                    variable[int(s)-1] = 1
            for s in stick:
                if s != '0':
                    variable[int(s)-1+4] = 1
            for s in situation:
                if s != '0':
                    variable[int(s)-1+9] = 1
            motion_variable[int(ID, 16)] = variable
    return motion_variable
    

def get_motion_variable2(name1:str,name2:str):
    """
    motion_variableの辞書を返す
    ワンホットエンコーディング
    """
    base = os.path.dirname(os.path.abspath(__file__))
    name = os.path.normpath(os.path.join(base, r'..\label.csv'))
    df = pd.read_csv(name, encoding="SHIFT-JIS", dtype = 'object')
    motion_variable = {}
    for name in ['0',name1,name2]:
        df_temp = df[[name, name+'button', name+'stick', name+'situation']].dropna(how='any')
        for _,ID,button,stick,situation in df_temp.itertuples(name=None):
            motion_variable[int(ID, 16)] = (button,stick,situation)
    # motion_variableのvalueを0からの番号にする
    converter = list(set(motion_variable.values()))
    motion_variable = {k: converter.index(v) for k,v in motion_variable.items()}
    
    return motion_variable


def yuzu_name_reset():
    """yuzuのウィンドウ名に割り振ったidを削除する"""
    infos_all = windbg.EnumWindows()    #info = [wName,wHandle,pid]
    infos = [info for info in infos_all if 'yuzu ' in info[0]]  #ウィンドウ名先頭5文字でyuzuを特定
    for info in infos:
        wName, wHandle, _ = info
        m = re.search(r'__(\d+)$', wName)
        if m:
            windbg.SetWindowText(wHandle, wName[:m.start()])

if __name__ == '__main__':
    player = ('11','23')
    label = get_label(*player)
    motion_variable = get_motion_variable(*player)
    motion_variable2 = get_motion_variable2(*player)
    a = len(next(iter(motion_variable.values())))
    a2 = max(motion_variable2.values())


    