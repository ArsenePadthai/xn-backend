import socket
import sys
from sqlalchemy import create_engine


#ENGINE = create_engine('mysql+pymysql://test:test@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)


def test_connection(host, port, batch_no, addr_no):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect((host, int(port)))
    print(f'success connected to {host}:{port}')

    # Session = sessionmaker(bind=ENGINE)
    # session = Session()

    # panel = session.query(SwitchPanel).filter(SwitchPanel.tcp_config.has(ip=ip)).first()
    data = bytes.fromhex('DA {} {} 86 86 86 EE'
                             .format(hex(int(batch_no))[2:].rjust(2, '0'),
                                     hex(int(addr_no))[2:].rjust(2, '0')))
    try:
        client.send(data)
        ret = client.recv(1024)
        print(ret)
        print(f'length is {len(ret)}')
    except Exception:
        print(f'failed to send query data to panel')
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == '__main__':
    args = sys.argv
    test_connection(args[1], int(args[2]), args[3], args[4])

