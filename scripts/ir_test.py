import socket
import sys


def scan_ir(ip_tail_list: list, addr: str):
    for ip_tail in ip_tail_list:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)
        client.connect((f'10.100.102.{ip_tail}', 4196))
        data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')
        client.send(data)
        try:
            m = client.recv(1024)
            print(m)
            print(ip_tail)
            client.close()
            break
        except:
            client.close()
            continue


if __name__ == '__main__':
    addr = sys.argv[1]
    ip_tails = sys.argv[2:]
    scan_ir(ip_tails, addr)