import logging
from ..utils import int2hex

L = logging.getLogger(__name__)


def query_ir_status(addr, conn):
    int_addr = addr
    hex_addr = int2hex(int_addr)
    data = bytes.fromhex(f"DA 00 {hex_addr} 86 86 86 EE")
    try:
        conn.send(data)
        recv = conn.recv(1024)
        L.info(recv)
        assert len(recv) == 8
        assert recv[1] == 0
        return recv[-2]
    except Exception as e:
        L.exception(e)
        L.error(f'failed to get ir status, int_addr {int_addr}, hex_addr {hex_addr}')
        return
