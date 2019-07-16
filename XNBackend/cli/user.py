import click
from flask.cli import AppGroup

user_cli = AppGroup('user')


@user_cli.command('create')
@click.option(
    '--level',
    type=click.Choice(['0', '1', '2', '3']),
    required=True,
    help='user permission level'
)
@click.argument(
    'username'
)
@click.argument(
    'password'
)
@click.argument(
    'person_id'
)
def create(level, username, password, person_id):
    from ..models import UserLogins, Users
    from ..models import db
    new_user = Users(person_id=person_id)
    db.session.add(new_user)
    db.session.flush()
    new_user_login = UserLogins(user_id=new_user.id,
                                username=username,
                                level=level)
    new_user_login.set_password(password)
    db.session.add(new_user_login)

    db.session.commit()
