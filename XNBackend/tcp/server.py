import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 51112

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

server.bind((bind_ip,bind_port))

print("[*] Listening on %s:%d" % (bind_ip,bind_port))

server.listen(5)

def handle_client(client_socket):
    request = client_socket.recv(1024)
    print("[*] Received: %s" % request)


while True:
    client,addr = server.accept()
    print("[*] Acception connection from %s:%d" % (addr[0],addr[1]))
    client_handler = threading.Thread(target=handle_client,args=(client,))
    client_handler.start()
