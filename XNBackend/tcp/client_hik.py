import socket
import time
from XNBackend.app import celery
from XNBackend.task.add import *

target_host = "127.0.0.1" 
target_port = 51112 


while True:
    try:
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((target_host,target_port))   
        a = mul_together.delay(3, 2).get()
        b = div_together.delay(8, 2).get()
        client.send(str(a+b).encode())
        #client.send(a)
        time.sleep(3)
    except BaseException:
        celery.control.broadcast('shutdown', destination='worker2@xn-hik.service')
        break







