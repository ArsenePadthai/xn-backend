from flask import Flask
import flask_restless
from flask_compress import Compress
from flask_log_request_id import RequestID
from XNBackend.tasks import celery
from XNBackend.app.filters import add_filters
from XNBackend.app.extensions import init_logger, init_cache, bcrypt, init_api
from XNBackend.models import db, HeatMapSnapshots, Users, UserLogins, AppearRecords, \
    LatestPosition, TrackingDevices, EnegyConsumeMonthly, EnergyConsumeDaily,\
    IRSensors, AQISensors, LuxSensors, FireAlarmSensors, Switches, Elevators, S3FC20, Relay
from XNBackend.extension import SaferProxyFix
from XNBackend.api import api_bp
from XNBackend.rest import dashboard_api_bp
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError
from XNBackend.cli import user_cli, systemd


def check_auth(*args, **kw):
    verify_jwt_in_request()


def auth_lg_1(*args, **kw):
    username = get_jwt_identity()
    user_login = UserLogins.query.filter_by(username=username).first()
    if user_login is None:
        raise NoAuthorizationError(u"请先登陆")
    elif user_login.level < 2:
        raise NoAuthorizationError(u'您没有足够的权限进行此操作!')


preprocessors = {
    "POST": [check_auth],
    "GET_SINGLE": [check_auth],
    "GET_MANY": [check_auth, auth_lg_1],
    "PATCH_SINGLE": [check_auth],
    "PATCH_MANY": [check_auth],
    "DELETE_SINGLE": [check_auth],
    "DELETE_MANY": [check_auth],
}


def create_app(config_filename=None):
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.wsgi_app = SaferProxyFix(app.wsgi_app)
    app.config.from_object('XNBackend.app.default_settings.DefaultConfiguration')
    app.config.from_envvar('XN_SETTINGS')
    if config_filename:
        app.config.from_pyfile(config_filename)

    RequestID(app)
    init_logger(app)
    celery.init_app(app)

    init_cache(app)

    # flask compress
    Compress(app)

    db.init_app(app)
    JWTManager(app)
    bcrypt.init_app(app)

    add_filters(app)

    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_api_bp)

    restless_manager = flask_restless.APIManager(app,
                                                 flask_sqlalchemy_db=db)
    JWTManager(app)
    app.cli.add_command(user_cli)
    app.cli.add_command(systemd)


    # flask_restless part
    restless_manager.create_api(LuxSensors, methods=["GET"])
    restless_manager.create_api(HeatMapSnapshots, methods=["GET"])
    restless_manager.create_api(Users, methods=["GET"])
    restless_manager.create_api(AppearRecords, methods=["GET"],
                                preprocessors=preprocessors)
    restless_manager.create_api(LatestPosition, methods=["GET"])
    restless_manager.create_api(TrackingDevices, methods=["GET"])
    restless_manager.create_api(EnegyConsumeMonthly, methods=["GET"])
    restless_manager.create_api(EnergyConsumeDaily, methods=["GET"])
    restless_manager.create_api(IRSensors, methods=["GET"])
    restless_manager.create_api(AQISensors, methods=["GET"])
    restless_manager.create_api(LuxSensors, methods=["GET"])
    restless_manager.create_api(FireAlarmSensors, methods=["GET"])
    restless_manager.create_api(Switches, methods=["GET"])
    restless_manager.create_api(Elevators, methods=["GET"])
    restless_manager.create_api(S3FC20, methods=["GET"])
    restless_manager.create_api(Relay, methods=["GET"])

    return app
