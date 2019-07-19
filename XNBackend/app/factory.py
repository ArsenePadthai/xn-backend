from flask import Flask
from flask_compress import Compress
from flask_log_request_id import RequestID
from XNBackend.task import celery
from XNBackend.app.filters import add_filters
from XNBackend.app.extensions import init_logger, init_cache, bcrypt, init_api
from XNBackend.models import db, LuxSensors, HeatMapSnapshots, Users, \
AppearRecords, LatestPosition, TrackingDevices, LatestCircuitRecord,\
CircuitBreakers, LatestAlarm, EnegyConsumeMonthly, EnergyConsumeDaily,\
IRSensors, AQISensors, LuxSensors, FireAlarmSensors, Switches, Elevators
from XNBackend.extension import SaferProxyFix
from flask_jwt_extended import JWTManager
from XNBackend.api import api_bp
import flask_restless
from flask_jwt_extended import JWTManager
from XNBackend.cli import user_cli


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

    restless_manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
    JWTManager(app)
    app.cli.add_command(user_cli)

    # flask_restless part
    restless_manager.create_api(LuxSensors, methods=["GET"])
    restless_manager.create_api(HeatMapSnapshots, methods=["GET"])
    restless_manager.create_api(Users, methods=["GET"])
    restless_manager.create_api(AppearRecords, methods=["GET"])
    restless_manager.create_api(LatestPosition, methods=["GET"])
    restless_manager.create_api(TrackingDevices, methods=["GET"])
    restless_manager.create_api(LatestCircuitRecord, methods=["GET"])
    restless_manager.create_api(CircuitBreakers, methods=["GET"])
    restless_manager.create_api(LatestAlarm, methods=["GET"])
    restless_manager.create_api(EnegyConsumeMonthly, methods=["GET"])
    restless_manager.create_api(EnergyConsumeDaily, methods=["GET"])
    restless_manager.create_api(IRSensors, methods=["GET"])
    restless_manager.create_api(AQISensors, methods=["GET"])
    restless_manager.create_api(LuxSensors, methods=["GET"])
    restless_manager.create_api(FireAlarmSensors, methods=["GET"])
    restless_manager.create_api(Switches, methods=["GET"])
    restless_manager.create_api(Elevators, methods=["GET"])

    return app
