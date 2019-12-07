import socket
import sys


def scan_ir():
    addr = ['a1', 'a4', '51', '9b', '9c', '6f', '6b', 'ac', '22', '6c',
            '53', '34', '05', '84', '06', '9a']
    addr = ['18', '03', '42', '25', '43', '12', 'A2', '27', '8D', '09', '97']
    ok_list = []
    for ad in addr:
        addr_no = ad
        for ip_tail in ['34', '35', '36']:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((f'10.100.102.{ip_tail}', 4196))
            data = bytes.fromhex(f'DA 00 {addr_no} 86 86 86 EE')
            client.send(data)
            try:
                m = client.recv(1024)
                assert m[1] == 0
                ok_list.append((addr_no, ip_tail))
                client.close()
                break
            except:
                client.close()
                continue
    import pprint
    pprint.pprint(ok_list)


if __name__ == '__main__':
    pass
    # addr = sys.argv[1]
    # ip_tails = sys.argv[2:]
    # scan_ir(ip_tails, addr)
