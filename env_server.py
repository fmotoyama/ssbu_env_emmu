# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 16:46:16 2022

@author: f.motoyama
"""
import struct, socket, threading, logging

from env import Env



class MySocket:
    def __init__(self, soc):
        self.soc = soc
        
    def mysend(self, msg):
        l = len(msg)
        totalsent = 0
        while totalsent < l:
            sent = self.soc.send(msg[totalsent:])
            assert sent, "socket broken"
            totalsent = totalsent + sent
    
    def myrecv(self, l):
        chunks = []
        bytes_recd = 0
        while bytes_recd < l:
            chunk = self.soc.recv(min(l - bytes_recd, 2048))    #ホストが死ぬと空白を受け取る
            assert chunk, "socket broken"
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)
    
    def mysend_plus(self,msg):
        # 長さ標識(2bytes)を含めて送信
        l = len(msg).to_bytes(2,'big')
        self.mysend(l)
        self.mysend(msg)
        
    def myrecv_plus(self):
        # 長さ標識(2bytes)を含めて受信
        l = self.myrecv(2)
        l = int.from_bytes(l,'big')
        return self.myrecv(l)
    
    def close(self):
        self.soc.close()



def loop_handler(mysocket):
    #　hostにenv_numを要求する
    mysocket.mysend_plus('req_env_num'.encode("UTF-8"))
    recv = mysocket.myrecv(1)
    env_num = int.from_bytes(recv, 'big')
    print(f'server {env_num}: connected')
    
    env = Env(env_num)
    env.get_emmu_Handles()
    
    
    while True:
        recv = mysocket.myrecv(1)
        operator = int.from_bytes(recv, 'big', signed=True)
        #print(f"operator:{operator},\ndata:{data}")
        
        if operator == 1:
            # step
            recv = mysocket.myrecv(1)
            action = int.from_bytes(recv, 'big')
            observation, reward, done, info = env.step(action)
            send = b''.join([
                observation.tobytes(),
                struct.pack('>f', reward),
                done.to_bytes(1,'big'),
                info['frame'].to_bytes(4,'big')
                ])
            mysocket.mysend(send)
        elif operator == 2:
            # legal actions
            send = bytes(env.legal_actions())
            mysocket.mysend_plus(send)
        elif operator == 3:
            # reset
            observation = env.reset()
            send = observation.tobytes()
            mysocket.mysend(send)
        elif operator == 4:
            # close
            env.close()
            mysocket.mysend_plus('closed'.encode("UTF-8"))
            print(f'server {env_num}: env close')
            break
        
        else:
            print(f'server {env_num}: unknown operator, {operator}')
            break
    
    
    mysocket.close()
    print('close')
    return 0







if __name__ == '__main__':
    # https://qiita.com/t_katsumura/items/a83431671a41d9b6358f    
    # ソケット通信(サーバー側)
    host = '192.168.11.18'
    #host = 'fmotoyama'
    port = 50000
    N = 1
    
    soc_sv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4,TCPを利用
    soc_sv.bind((host, port))                                   # ソケットにアドレスを割り当てる
    soc_sv.listen(N)                                            # N個のホストを待ち受ける
    soc_sv.settimeout(20)
    print('ready')
    
    # ホストにloop_handlerを割り当てる
    threads = []
    for _ in range(N):
        try:
            soc, address = soc_sv.accept()
            soc.settimeout(180)
            mysocket = MySocket(soc)
        except Exception as e:
            soc_sv.close()
            logging.exception('error', stack_info=True)
            raise e
        
        threads.append(threading.Thread(
            target=loop_handler,
            args=(mysocket,),
            daemon=True
            ))
        threads[-1].start()
    
    # loop_handlerの処理として、hostから要求を受けenv_paramを返す
    #[thread.start() for thread in threads]
    [thread.join() for thread in threads]
    soc_sv.close()
    """
    #接続要求を受信
    soc, address = soc_sv.accept()
    mysocket = MySocket(soc)
    
    loop_handler(MySocket(soc), 0)
    
    soc_sv.close()
    #"""
    


"""
print('waiting')
soc, address = socket.accept()
"""

#sudo rm -rf ssbu/workshape/muzero/results/ssbu
#tensorboard --logdir \\wsl.localhost\Ubuntu-20.04\home\fmotoyama\ssbu\workshape\muzero\results
