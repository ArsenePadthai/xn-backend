import socket
import sys
import time


def scan_ir(ip_tail: str, addr: str):
    # for ip_tail in ip_tail_list:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)
    ip = f'10.100.102.{ip_tail}'
    try:
        client.connect((ip, 4196))
    except:
        return
    data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')
    time.sleep(0.5)
    client.send(data)
    try:
        m = client.recv(1024)
        print(m.hex())
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


def scan_4_floor_ir():
    add_ip = {
        "A1": 15,
        "6B": 15,
        "9A": 15,
        "7B": 15,
        "14": 15,
        "06": 15,
        "84": 15,
        "05": 15,
        "34": 15,
        "AC": 15,
        "53": 15,
        "6C": 15,
        "22": 15,
        "44": 11,
        "5E": 11,
        "41": 11,
        "6F": 15,
        "9C": 15,
        "9B": 15,
        "2B": 9,
        "51": 15,
        "28": 12,
        "85": 12,
        "7F": 12,
        "A4": 15,
        "7E": 11,
        "6E": 11,
        "96": 11
    }


def scan_3_floor_ir():
    add_ip = {
        "80": 84,
        "5b": 84,
        "61": 84,
        "20": 84,
        "60": 84,
        "40": 84,
        "8C": 84,
        "78": 84,
        "AF": 84,
        "87": 83,
        "74": 83,
        "75": 83,
        "46": 83,
        "67": 83,
        "70": 83,
        "94": 81,
        "72": 83,
        "A0": 81,
        "57": 83,
        "A8": 81,
        "89": 83
    }
    fail = []
    for k, v in add_ip.items():
        m=scan_ir(v, k)
        if m != 1:
            fail.append(k)
    print(fail)




if __name__ == '__main__':
   addr = sys.argv[1]
   ips = sys.argv[2:]
   for ip in ips:
       ret = scan_ir(ip, addr)
       if ret==1:
           break
