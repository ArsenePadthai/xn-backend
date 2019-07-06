import socket
import random
from XNBackend.task import celery


target_host = "127.0.0.1" 
target_port = 51113 
hik_client = None


def tcp_hik():
    global hik_client 
    if hik_client is None:   
        hik_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        hik_client.connect((target_host,target_port))   
    return hik_client
    

def send_to_hik(data):
    global hik_client 
    try:
        client = tcp_hik()
        client.send(str(data).encode()[:-1])
        client.send(str(data).encode()[-1:])
        '''
        Prevent connections from closing too fast and the RESET package sent by TCP will not be received.
        '''
    except OSError:
        celery.control.broadcast('shutdown', destination=['worker1@xn-hik.service'])
        hik_client = None
    data_byte = client.recv(1024)
    return data_byte

    
@celery.task()
def network_relay_query():
    id_bytes = bytes.fromhex(hex(random.randint(1, 65535))[2:].rjust(4, '0'))
    data = bytes.fromhex('CC') + id_bytes + bytes.fromhex('FE EE')
    message = send_to_hik(data)
    return str(message)   

 
@celery.task()
def sub_together(a, b):
    data = a - b
    send_to_hik(data)
    return data 

