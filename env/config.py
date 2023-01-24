# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 22:59:38 2021

@author: motoyama
"""


#a_heapfree_chain = [0x52C2070,0x670], mymod1
ra_free = 0x392C64B4 + 0xc  # yuzu1022
#ra_free = 0x372C64B4 + 0xc  # yuzu1313
#前0x10と0x90が空き

chains = {

#座標
'posx1':'float',
'posy1':'float',
'posx2':'float',
'posy2':'float',
#パーセント
'per1':'float',
'per2':'float',
#残りジャンプ回数
'jmp_remain1':'int',
'jmp_remain2':'int',
#シールド残量
'shield_remain1':'float',
'shield_remain2':'float',
#向いている方向
'dir1':'int',
'dir2':'int',
#無敵の有無
'invincible1':'int',
'invincible2':'int',

#モーションID
'motionID1':'int',
'motionID2':'int',
#シーンID
'sceneID':'int',
#試合経過フレーム　GOからカウント 対戦が終わると値を保持　対戦ロード中に0に初期化
'frame':'int',

'loss1':'int',
'loss2':'int',

}





















