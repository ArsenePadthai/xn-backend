import click
import os 
from flask.cli import AppGroup
from XNBackend.models import TcpConfig, SwitchPanel

systemd = AppGroup('systemd')


@systemd.command()
@click.option(
    '--code',
    type=click.Choice(['start', 'stop']),
    required=True,
    help='start or stop celery worker'
)
def control(code):
    os.system('sudo systemctl {} xn-sensor@relay.service'.format(code))
    for tcp in TcpConfig.query.order_by():
        if tcp.ip in ['10.100.102.3'] or '10.100.101' in tcp.ip:
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
