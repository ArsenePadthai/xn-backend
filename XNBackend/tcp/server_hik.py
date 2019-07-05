import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 51113

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind((bind_ip,bind_port))
server.listen(5)
client,addr = server.accept()
while True:
    print("[*] Acception connection from %s:%d" % (addr[0],addr[1]))
    data = client.recv(1024)
    print(data.decode())
