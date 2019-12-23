import sys
import socket


def check_aqi(ip_tail, addr):
    ip = f'10.100.102.{ip_tail}'
    port = 4196
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)
    client.connect((ip, 4196))
    import time
    time.sleep(1)
    data = bytes.fromhex(f'DA 06 {addr} 86 86 86 EE')
    client.send(data)
    try:
        m = client.recv(1024)
        print(m)
        print(ip)
        print(addr)
        client.close()
    except Exception as e:
        print(e)
        client.close()


if __name__ == '__main__':
    addr = sys.argv[1]
    ip = sys.argv[2]
    check_aqi(ip, addr)

