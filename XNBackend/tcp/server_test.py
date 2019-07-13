import socket
import threading
import binascii


def relay_send(data1_bytes):
    data0_bytes = bytes.fromhex('BB')
    data2_bytes = bytes.fromhex('01 02 03 EE')
    client.send(data0_bytes+data1_bytes+data2_bytes) 
    

def infrared_send(data1_bytes):
    data0_bytes = bytes.fromhex('DB')
    data2_bytes = bytes.fromhex('00 01 EE')
    client.send(data0_bytes+data1_bytes+data2_bytes)
    

def aqi_send(data1_bytes):
    data0_bytes = bytes.fromhex('DD')
    data2_bytes = bytes.fromhex('03 01 0A 02 A2 22 3A AD 4C 3A 66 54 EE')
    client.send(data0_bytes+data1_bytes+data2_bytes) 
    

def lux_send(data1_bytes):
    data0_bytes = bytes.fromhex('DF')
    data2_bytes = bytes.fromhex('00 00 00 62 9A 33 EE')
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
        #relay_send(data[1:3])
        #infrared_send(data[1:6])
        aqi_send(data[1:6])
        #lux_send(data[1:6])
except Exception:
    server.close()


