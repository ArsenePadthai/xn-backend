import socket


def get_panel_client(ip, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect((ip, port))
    return client


def query_panel_status(client, ip, batch_no, addr_no):
    data = bytes.fromhex('DA {} {} 86 86 86 EE'.format(
        hex(int(batch_no))[2:].rjust(2, '0'),
        hex(int(addr_no))[2:].rjust(2, '0'))
                         )
    client.send(data)
    ret = client.recv(1024)
    return ret
