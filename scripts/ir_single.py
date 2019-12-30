import socket
import sys
import time


def scan_ir(ip_tail: str, addr: str):
    # for ip_tail in ip_tail_list:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)
    ip = f'10.100.102.{ip_tail}'
    print(ip)
    client.connect((ip, 4196))
    data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')
    time.sleep(0.5)
    client.send(data)
    try:
        m = client.recv(1024)
        assert m[1] == 0
        print(f'hex addr {addr}, ip tail {ip_tail}', 'pass')
        client.close()
        return 1
    except Exception as e:
        print(e)
        print(addr, 'failed')
        client.close()
        return 0


def scan_6_floor_ir():
    ip_tail = [34, 35, 36]
    addr = ['8d', '09', '97', '2a', '07', '17', '4d', '45', 'b6', '3d',
            '1c', '2e', '3c', '08', '13', 'ae', 'a5', '8e', '49', '92', '2b', '1d', '1b', '30']
    ok = []
    for a in addr:
        for ip in ip_tail:
            m = scan_ir(ip, a)
            if m == 1:
                ok.append(a)
                break
    print(ok)


if __name__ == '__main__':
   addr = sys.argv[1]
   ips = sys.argv[2:]
   for ip in ips:
       ret = scan_ir(ip, addr)
       if ret==1:
           break
