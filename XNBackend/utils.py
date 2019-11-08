import socket


def query_panel_status(ip, batch_no, addr_no):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect((ip, 4196))
    data = bytes.fromhex('DA {} {} 86 86 86 EE'.format(
        hex(int(batch_no))[2:].rjust(2, '0'),
        hex(int(addr_no))[2:].rjust(2, '0'))
                         )
    try:
        client.send(data)
        ret = client.recv(1024)
        client.close()
        return ret
    except Exception as e:
        print(e)
        client.close()
