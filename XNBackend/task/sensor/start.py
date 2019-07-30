import os 
from XNBackend.app.entry import app 
from XNBackend.models.models import TcpConfig


def startWorker():
    with app.app_context(): 
        os.system('sudo systemctl start xn-sensor@sensor.service')
        for tcp in TcpConfig.query.order_by():
            addr = tcp.ip + ':' + str(tcp.port)
            os.system('sudo systemctl start xn-sensor@{}.service'.format(addr))


if __name__ == '__main__':
    startWorker()
