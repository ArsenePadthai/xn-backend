import click
import os 
from flask.cli import AppGroup
from XNBackend.models.models import TcpConfig

systemd = AppGroup('systemd')


@systemd.command()
@click.option(
    '--code',
    type=click.Choice(['start', 'stop']),
    required=True,
    help='start or stop celery worker'
)
def control(code):
    os.system('sudo systemctl {} xn-sensor@sensor.service'.format(code))
    for tcp in TcpConfig.query.order_by():
        addr = tcp.ip + ':' + str(tcp.port)
        click.echo('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
        os.system('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
