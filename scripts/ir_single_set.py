import socket
import sys
import time


def scan_ir(ip_tail: str, addr: str):
    # for ip_tail in ip_tail_list:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)
    client.connect((f'10.100.102.{ip_tail}', 4196))
    data = bytes.fromhex(f'DA 00 {addr} 03 ff ee')
    time.sleep(0.5)
    client.send(data)
    try:
        m = client.recv(1024)
        print(addr, 'pass')
        print(m.hex())
        client.close()
    except Exception as e:
        print(e)
        print(addr, 'failed')
        client.close()


if __name__ == '__main__':
    ip_tail = sys.argv[2]
    addr = sys.argv[1]
    scan_ir(ip_tail, addr)
