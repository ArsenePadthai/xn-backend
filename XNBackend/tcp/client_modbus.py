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
        a = add_together.delay(1, 2).get()
        b = sub_together.delay(39, 17).get()
        client.send(str(a+b).encode())
        #client.send(a)
        time.sleep(3)
    except BaseException:
        celery.control.broadcast('shutdown', destination='worker1@hk-modbus.service')
        break







