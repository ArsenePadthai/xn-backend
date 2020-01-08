import struct
import logging
from ..utils import int2hex
import time

L = logging.getLogger(__name__)


def parse_aqi_return(data):
    co2 = struct.unpack('>H', data[3:5])[0]
    tvoc = struct.unpack('>H', data[5:7])[0]
    hcho = struct.unpack('>H', data[7:9])[0]
    pm25_high = data[9]
    pm25_low = data[10]
    hum_high = data[11]
    hum_low = data[12]
    tem_high = data[13]
    tem_low = data[14]

    hcho = round(hcho*0.0012, 2)
    ad_for_pm25 = pm25_high*256 + pm25_low
    cal_voltage = ad_for_pm25 * 5/1024
    dust_density = round(0.17*cal_voltage - 0.1, 2)
    hum = (hum_high*256 + hum_low)/10
    tem = (tem_high*256 + tem_low)/10

    return co2, tvoc, hcho, max(dust_density, 0), hum, tem


def query_aqi_value(addr, conn):
    int_addr = addr
    hex_addr = int2hex(int_addr)
    data = bytes.fromhex(f"DA 06 {hex_addr} 86 86 86 EE")
    try:
        time.sleep(1)
        conn.send(data)
        recv = conn.recv(1024)
        assert len(recv) == 16
        return parse_aqi_return(recv)
    except Exception as e:
        L.error(e)
        L.error(data.hex())
        L.error(conn.getpeername())
        L.error(f'failed to get aqi status, int_addr {int_addr}, hex_addr {hex_addr}')
        return
