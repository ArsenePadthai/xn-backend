from flask import Flask
from flask_compress import Compress
from flask_log_request_id import RequestID
from XNBackend.task import celery
from XNBackend.app.filters import add_filters
from XNBackend.app.extensions import init_logger, init_cache, bcrypt, init_api
from XNBackend.models import db, LuxSensors
from XNBackend.extension import SaferProxyFix
from flask_jwt_extended import JWTManager
from XNBackend.api import api_bp
import flask_restless


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
    restless_manager.create_api(LuxSensors, methods=["GET"])

    return app
