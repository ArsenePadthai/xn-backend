import click
import os
from flask.cli import AppGroup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from XNBackend.models import SwitchPanel, IRSensors

systemd = AppGroup('systemd')
ENGINE = create_engine('mysql+pymysql://xn:Pass1234@127.0.0.1:3306/xn?charset=utf8mb4', echo=True)
Session = sessionmaker(bind=ENGINE)
session = Session()


@systemd.command()
@click.option(
    '--code',
    type=click.Choice(['start', 'stop', 'restart', 'enable']),
    required=True,
    help='start or stop celery worker'
)
def control(code):
    Panels = session.query(SwitchPanel)
    # Irs = session.query(IRSensors)

    ip_list = []
    for p in Panels:
        if p.tcp_config and p.tcp_config.ip not in ip_list:
            ip_list.append(p.tcp_config.ip)

    # for i in Irs:
    #     if i.tcp_config and i.tcp_config.ip not in ip_list:
    #         ip_list.append(i.tcp_config.ip)

    os.system('sudo systemctl {} xn-sensor@relay.service'.format(code))
    for ip in ip_list:
        addr = ip + ':' + '4196'
        click.echo('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
        os.system('sudo systemctl {0} xn-sensor@{1}.service'.format(code, addr))
