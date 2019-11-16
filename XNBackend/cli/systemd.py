import click
import os 
from flask.cli import AppGroup
from XNBackend.models import TcpConfig, SwitchPanel

systemd = AppGroup('systemd')

ip_list = [
    '10.100.102.1',
    '10.100.102.2',
    '10.100.102.3',
    '10.100.102.4',
    '10.100.102.5',
    '10.100.102.41',
    '10.100.102.42',
    '10.100.102.43',
    '10.100.102.44',
    '10.100.102.33',
#    '10.100.102.9',
#    '10.100.102.10',
#    '10.100.102.12',
    '10.100.102.13',
    '10.100.102.14',
    '10.100.102.15',
    '10.100.102.16',
#    '10.100.102.81',
    '10.100.102.82',
#    '10.100.102.83',
#    '10.100.102.84',
    '10.100.102.85',
    '10.100.102.86',
    '10.100.102.87',
    '10.100.102.88',
    '10.100.102.17',
    '10.100.102.18',
    '10.100.102.19',
    '10.100.102.20',
    '10.100.102.21',
    '10.100.102.25',
    '10.100.102.26',
]

@systemd.command()
@click.option(
    '--code',
    type=click.Choice(['start', 'stop', 'restart', 'enable']),
    required=True,
    help='start or stop celery worker'
)
def control(code):
    os.system('sudo systemctl {} xn-sensor@relay.service'.format(code))
    for tcp in TcpConfig.query.order_by():
        #if tcp.ip in ['10.100.102.3'] or '10.100.101' in tcp.ip:
        if tcp.ip not in ip_list:
            continue
        addr = tcp.ip + ':' + str(tcp.port)
        click.echo('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
        os.system('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
'''
def control(code):
    os.system('sudo systemctl {} xn-sensor@sensor.service'.format(code))
    tcp_config_ids = SwitchPanel.query.filter(
        SwitchPanel.tcp_config_id!=None
        ).with_entities(
            SwitchPanel.tcp_config_id
            ).distinct().all()
    
    tcp_config_ids = [i[0] for i in tcp_config_ids]
    ret = TcpConfig.query.filter(TcpConfig.id.in_(tcp_config_ids)).all()
    for tcp in ret:
        # 46 not online
        # 47 has no response
        # remove ========================================== later
        if tcp.ip in ['10.100.102.46', '10.100.102.47']:
            continue
        addr = tcp.ip + ':' + str(tcp.port)
        click.echo('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
        os.system('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
'''
