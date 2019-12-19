import os
import time
import logging
from threading import Thread

L = logging.getLogger()

def test_ping(ip_addr):
    while True:
        try:
            os.system(f'ping -c 2 10.100.101.{ip_addr}')
        except:
            L.exception('ping pong failed')
        time.sleep(40)


def batch_ping():
    t_queue = []
    for i in range(1, 91):
        t_queue.append(Thread(target = test_ping, args=(i,)))
    for t in t_queue:
        t.start()

        

if __name__ == '__main__':
    batch_ping()
