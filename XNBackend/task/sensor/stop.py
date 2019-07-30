import os 
from XNBackend.app.entry import app 
from XNBackend.models.models import TcpConfig


def stopWorker():
    with app.app_context(): 
        os.system('sudo systemctl stop xn-sensor@sensor.service')
        for tcp in TcpConfig.query.order_by():
            addr = tcp.ip + ':' + str(tcp.port)
            os.system('sudo systemctl stop xn-sensor@{}.service'.format(addr))


if __name__ == '__main__':
    stopWorker()
