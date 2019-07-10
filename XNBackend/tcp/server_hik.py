import socket
import threading
import binascii


def relay_send(id, data):
    data0_bytes = bytes.fromhex('BB')
    data1_bytes = bytes.fromhex(id)
    data2_bytes = bytes.fromhex(data)
    client.send(data0_bytes+data1_bytes+data2_bytes) 
    

def infrared_send(address, data):
    data0_bytes = bytes.fromhex('DB')
    data1_bytes = data1.encode()
    data2_bytes = bytes.fromhex(data)
    client.send(data0_bytes+data1_bytes+data2_bytes) 
    

def aqi_send(address, data):
    data0_bytes = bytes.fromhex('DD')
    data1_bytes = data1.encode()
    data2_bytes = bytes.fromhex(data)
    client.send(data0_bytes+data1_bytes+data2_bytes) 
    

def illum_send(address, data):
    data0_bytes = bytes.fromhex('DF')
    data1_bytes = address.encode()
    data2_bytes = bytes.fromhex(data)
    client.send(data0_bytes+data1_bytes+data2_bytes) 


bind_ip = "0.0.0.0"
bind_port = 51113

try:
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((bind_ip,bind_port))
    server.listen(5)
    client,addr = server.accept()
    while True:
        print("[*] Acception connection from %s:%d" % (addr[0],addr[1]))
        data = client.recv(1024)
        print(data)
        relay_send('00 04', '01 01 00 EE')
except Exception:
    server.close()


'''
    data0 = 'DF'
    data1 = '000A010101'
    data2 = '00 00 00 00 10 11 EE'
'''
