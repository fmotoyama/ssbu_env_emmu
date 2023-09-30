# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 22:56:19 2023

@author: fmotoyama
"""
import random, re
import numpy as np

from env import windbg
from env.env import Env


def get_action_name(action):
    action_shape = (6,9,2)
    # [null,A,B,X(大ジャンプ),X(+Y,小ジャンプ),R,ZL]
    btn_name = ['・ ','A ','B ','X ','R ','ZL']
    #[null,8方向]
    stk1_name = ['・ ','→ ','↗ ','↑ ','↖ ','← ','↙ ','↓ ','↘ ',]
    stk2_name = ['・ ','shift']
    ids = np.ravel(np.where(
        np.arange(np.prod(action_shape)).reshape(*action_shape) == action
    ))
    return(btn_name[ids[0]],stk1_name[ids[1]],stk2_name[ids[2]])

def yuzu_name_reset():
    """yuzuのウィンドウ名に割り振ったidを削除する"""
    infos_all = windbg.EnumWindows()    #info = [wName,wHandle,pid]
    infos = [info for info in infos_all if 'yuzu ' in info[0]]  #ウィンドウ名先頭5文字でyuzuを特定
    for info in infos:
        wName, wHandle, _ = info
        m = re.search('__(\d+)$', wName)
        if m:
            windbg.SetWindowText(wHandle, wName[:m.start()])


if __name__ == '__main__':
    
    e = Env(0)
    e.get_emmu_Handles()
    e.reset()
    frame1 = 0
    while True:
        data = e.read_memory.peek_collected_param()
        frame2 = data['frame']
        gap = frame2 - frame1
        if gap == 0:
            continue
        frame1 = frame2
        
        #a = e.legal_actions()
        action = random.choice(e.legal_actions())
        action = 0
        observation, reward, done, _ = e.step(action)
        
        #print(f'\rgap:{str(gap).rjust(5)}, reward:{str(round(reward, 5)).rjust(10)}',end = '')
        
        if done:
            e.close()
            break