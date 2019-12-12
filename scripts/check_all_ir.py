from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from XNBackend.models import IRSensors, TcpConfig
import socket


def check_all(floor):
    ENGINE = create_engine('mysql+pymysql://xn:Pass1234@10.100.101.199:3306/xn?charset=utf8mb4')
    Session = sessionmaker(bind=ENGINE)
    session = Session()
    all_ir = session.query(IRSensors).filter(IRSensors.locator_body.has(floor=floor)).order_by(IRSensors.tcp_config_id)
    print(all_ir)
    wrong_list = []
    for ir in all_ir:
        addr = hex(ir.addr_no).lstrip('0x').rjust(2, '0')
        ip = ir.tcp_config.ip
        print(addr)
        data = bytes.fromhex(f'DA 00 {addr} 86 86 86 EE')
        try:
            assert client
            assert client.getpeername()[0] == ip
        except (NameError, AssertionError):
            try:
                client.close()
            except:
                pass
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((ip, 4196))
        client.send(data)
        try:
            m = client.recv(1024)
            assert m[1] == 0
            print(m)
        except AssertionError as e:
            print(e)
            wrong_list.append((ir.id, addr, int('0x'+addr, 0), ip))
        except Exception as e:
            print(e)
            wrong_list.append((ir.id, addr, int('0x'+addr, 0), ip))
    import pprint
    pprint.pprint(wrong_list)


if __name__ == "__main__":
    pass