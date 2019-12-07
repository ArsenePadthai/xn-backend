import socket
import sys


def scan_ir(ip_tail: str, addr: str):
    # for ip_tail in ip_tail_list:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)
    client.connect((f'10.100.102.{ip_tail}', 4196))
    data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')
    client.send(data)
    try:
        m = client.recv(1024)
        print(addr, 'pass')
        print(ip_tail)
        client.close()
    except:
        print(addr, 'failed')
        client.close()


if __name__ == '__main__':
    ip_tails = sys.argv[1]
    m = ['18', '03', '42', '25', '43', '12', 'A2', '27', '8D', '09', '97', '2a', '17', '4d', '45', 'b6',
         '3d', '1c', '2e', '3c', '08', '13', 'ae', '8e', 'b3', '37', '2b', '1d', '4c', '35']
    m=['30']
    for ad in m:
        scan_ir(ip_tails, ad)

