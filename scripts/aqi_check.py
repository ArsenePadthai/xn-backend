import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(5)
client.connect(('192.168.58.10', 4196))

data = bytes.fromhex('DC 5 07 86 86 86 EE')

client.send(data)
a = client.recv(1024)

print(a)