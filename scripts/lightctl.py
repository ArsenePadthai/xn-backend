import time
import socket
import logging
from struct import pack
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from XNBackend.models import Relay


ENGINE = create_engine('mysql+pymysql://test:test@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)

L = logging.getLogger()


def light_all_on():
    Session = sessionmaker(bind=ENGINE)
    session = Session()

    all_relays = session.query(Relay).order_by(Relay.id.asc()).all()
    m = list(all_relays)
    code = '32'
    while True:
        L.info('==========================')
        L.info(len(m))
        L.info('==========================')
        for relay in m:
            if relay.addr and relay.tcp_config:
                data = bytes.fromhex('55') + pack('>B', relay.addr) + bytes.fromhex(code + '00 00 00') + pack('>B', relay.channel) + bytes.fromhex(hex(int(code, 16) + 85 + relay.addr + relay.channel)[-2:])
                client_so = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                client_so.settimeout(10)
                try:
                    client_so.connect((relay.tcp_config.ip, relay.tcp_config.port))
                except Exception as e:
                    L.exception(f"failed to connect to {relay.tcp_config.ip}, reason: {e}")
                    continue
                try:
                    client_so.send(data)
                    m.remove(relay)
                except Exception as e:
                    L.exception(e)
                finally:
                    try:
                        client_so.close()
                    except:
                        pass
        time.sleep(60)

if __name__ == '__main__':
    light_all_on()
