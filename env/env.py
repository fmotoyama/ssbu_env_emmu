# -*- coding: utf-8 -*-
"""
Created on Tue May 24 16:15:17 2022

@author: f.motoyama
"""
import time
import numpy as np

#import os, sys
#sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from . import windbg, utils
from .read_memory import ReadMemory
from .controller import Controller
from .controller import KeyValue as K



class Env_param:
    def __init__(self):
        # 対戦カード
        self.player = ('11','23') #1p:ファルコン,2p:ガノン
        # 自分のポート番号 1か2しか使ってはいけない
        self.port = 1
        
        # モーションを表す変量
        self.motion_variables = utils.get_motion_variable(*self.player)        
        self.motion_variables_length = len(next(iter(self.motion_variables.values())))
        #環境データの形状 2player * [x座標,y座標,パーセント,シールド残量,ジャンプ残り回数,向き,無敵,モーション]
        self.observation_shape = (2,9+self.motion_variables_length)
        
        # [null,A,B,X,R,ZL]
        bottun_lists = {
            1:[[], [K.A], [K.B], [K.X], [K.R], [K.ZL]],
            2:[[], [K.A2], [K.B2], [K.X2], [K.R2], [K.ZL2]]
            }
        # [null,4方向]
        stick_lists = {
            1: [[],[K.right],[K.up],[K.left],[K.down]],
            2: [[],[K.right2],[K.up2],[K.left2],[K.down2]]
            }
        
        self.bottun_list = bottun_lists[self.port]
        self.stick_list = stick_lists[self.port]
        self.action_shape = (len(self.bottun_list),len(self.stick_list))
        


class Env(Env_param):
    def __init__(self, env_num):
        super().__init__()
        self.env_num = env_num


    def get_emmu_Handles(self):
        """開いている全てのエミュのpHandle,wcHandleを求め、env_numに従って選ぶ"""
        pids = windbg.get_pids('yuzu.exe')
        pHandles = [windbg.get_pHandle(pid) for pid in pids]
        # wHandleの取得　info=[ウィンドウ名,wHandle,pid]
        infos_all = windbg.EnumWindows()
        infos = [info for info in infos_all if 'yuzu ' in info[0]]  # ウィンドウ名先頭5文字でyuzuを特定
        # wcHandleを取得し、pidでpHandleと対応づける
        Handles = []
        for wName,wHandle,pid in infos:
            pHandle = pHandles[pids.index(pid)]
            wcHandle = windbg.EnumChildWindows(wHandle)[3]  # yuzu1022:3
            #wcHandle = windbg.EnumChildWindows(wHandle)[4]  # yuzu1268:4
            windbg.SetWindowText(wHandle, wName + '__' + str(pids.index(pid)))
            Handles.append((pHandle,wcHandle))
        
        pHandle, wcHandle = Handles[self.env_num]
        self.read_memory = ReadMemory(pHandle)
        self.controller = Controller(wcHandle)
    
    
    def TrainingMode_reset(self):
        self.controller.TrainingMode_reset()
        
    def TrainingMode_enemy_activate(self):
        # cupを起動
        self.controller.TrainingMode_enemy_activate()
        time.sleep(0.5)
    
    def TrainingMode_enemy_deactivate(self):
        # cupを停止
        self.controller.TrainingMode_enemy_deactivate()
        time.sleep(0.1)
    
    
    def reset(self):
        self.controller.set_neutral()
        self.pressed_button = set()     # 0は入れない
        self.pressed_stick = set()
        
        """
        while True:
            self.controller.TrainingMode_reset()
            time.sleep(0.2)
            data = self.read_memory.peek_collected_param()
            if data['per1'] == 0 and data['per2'] == 0:
                break
        """
        observation = self.get_observation()
        
        self.start_frame = self.data['frame']            # 対戦の開始F
        # step()で更新
        self.frame = self.data['frame']                  # 現在F
        self.per = [self.data['per1'],self.data['per2']]      # 現在パーセント
        # get_observation()で更新
        self.stock = [3,3]                          # 現在ストック
        self.loss = [self.data['loss1'],self.data['loss2']]   # 総撃墜回数
        self.end = 0                                # 終了判定 0/1/2 → 未決着/1p勝利/2p勝利
        return observation
    
    
    def step(self,action):
        idxs = np.ravel(np.where(
            np.arange(np.prod(self.action_shape)).reshape(self.action_shape) == action
        ))
        #button_id = action // 18    # 行　0~6
        #stick_id = action % 18      # 列　0~17
        button_input = self.bottun_list[idxs[0]]
        stick_input = self.stick_list[idxs[1]]
        """
        assert idxs.shape == (3,)
        if idxs[2]:
            stick_input = stick_input + [self.stick_shift]  # +=で書くとstick_listに追加される
        """
        
        press = stick_input + button_input
        release = list(self.pressed_stick - set(stick_input)) + \
                  list(self.pressed_button - set(button_input))
        self.pressed_stick = set(stick_input)
        self.pressed_button = set(button_input)
        for value in release:
            self.controller.keyRelease(value)
        for value in press:
            self.controller.keyPress(value)
        
        
        # 環境の取得 !!!actionが実行された後かはわからない
        observation = self.get_observation()
        # フレームが前stepから変化していないとき、待機
        if self.frame == self.data['frame']:
            time.sleep(1/60)
            observation = self.get_observation()
        self.frame = self.data['frame']
        
        # 終了判定 0/1/2 → 未決着/1p勝利/2p勝利
        if self.loss[0] + 1 == self.data['loss1']:
            # 1pの死亡回数が増えていた場合
            self.end = 2
            self.loss[0] += 1
            self.stock[0] -= 1
        elif self.loss[1] + 1 == self.data['loss2']:
            # 2pの死亡回数が増えていた場合
            self.end = 1
            self.loss[1] += 1
            self.stock[1] -= 1
        else:
            self.end = 0
        
        # actorに送るデータをまとめる　以下のデータは自分（self.port）が基準
        if self.port == 2:
            observation = np.flipud(observation)
        if self.end:
            reward = 1 if self.end == self.port else -1*0.5
        else:
            #(与えたダメージ-受けたダメージ)/100の報酬
            reward = ((self.data[f'per{3-self.port}'] - self.per[2-self.port])
                      - (self.data[f'per{self.port}'] - self.per[self.port-1])*0.5)/100
            self.per = [self.data['per1'],self.data['per2']]
        done = bool(self.end)
        info = {'frame': self.data['frame']}

        return observation, reward, done, info
    
    def legal_actions(self):
        return list(range(np.prod(self.action_shape)))
    
    def close(self):
        time.sleep(0.1)
        self.controller.set_neutral()
        self.reset()
        del self.read_memory, self.controller


    def get_observation(self):
        """
        observation[port1/port2] = [x座標,y座標,パーセント,シールド残量,ジャンプ残り回数,向き,無敵,モーション]
        (敵ベクトル,崖ベクトル1,崖ベクトル2,技hitフラグ)
        """
        self.data = self.read_memory.peek_collected_param()
        
        observation = np.zeros(self.observation_shape, dtype = 'f4')
        for port in [1,2]:
            x_dis = self.data[f'posx{3-port}']-self.data[f'posx{port}']
            y_dis = self.data[f'posy{3-port}']-self.data[f'posy{port}']
            observation[port-1,:9] = [
                self.data[f'posx{port}']/200,
                self.data[f'posy{port}']/200,
                self.data[f'per{port}']/100,
                self.data[f'shield_remain{port}']/50,
                self.data[f'jmp_remain{port}']/2,
                self.data[f'dir{port}'],
                self.data[f'invincible{port}'] not in [7,13],    # 無敵フラグ
                np.sqrt(x_dis**2 + y_dis**2)/200,
                np.degrees(np.arctan2(x_dis, y_dis))/180 #上が0,下が±180
                ]
            variable = self.motion_variables.get(self.data[f'motionID{port}'])
            if variable == None:
                variable = np.zeros(self.motion_variables_length)
            observation[port-1,9:] = variable
        
        return observation
    
    def get_delay():
        """
        ジャンプの入力から観測まで何Fかかるか計測する
        踏み切りは全キャラ共通で3F
        """
        pass


class Env_dummy(Env_param):
    def __init__(self,seed:int):
        super().__init__()

    def reset(self):
        return self.get_observation()
    
    def step(self,action):
        observation = np.zeros(self.observation_shape, dtype = 'f4')
        if action == 0:
            reward = 1
            done = 1
        else:
            reward = 0
            done = 0
        return observation, reward, done
    
    def legal_actions(self):
        return list(range(np.prod(self.env.action_shape)))
    
    def close(self):
        pass




if __name__ == '__main__':
    pass
