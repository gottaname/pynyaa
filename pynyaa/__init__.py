
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_login import LoginManager

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config: str) -> Flask:
    app = Flask(__name__, static_folder='assets/static')
    app.config.from_pyfile(str(config))

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    init_blueprints(app)
    init_jinja_env(app)
    init_hooks(app)
    init_login(app)

    return app


def init_blueprints(app: Flask):
    from . import views
    app.register_blueprint(views.main)
    app.register_blueprint(views.userbp)
    app.register_blueprint(views.api, url_prefix='/api/v1')

    app.errorhandler(404)(views.errors.page_not_found)


def init_jinja_env(app: Flask):
    from . import utils
    app.jinja_env.filters['pretty_size'] = utils.pretty_size
    app.jinja_env.filters['cdatasafe'] = utils.cdatasafe
    app.jinja_env.filters['bootstrap_alert'] = utils.bootstrap_alert
    app.jinja_env.globals['url_for_other_page'] = utils.url_for_other_page
    app.jinja_env.finalize = lambda val: '' if val is None else val


def init_hooks(app: Flask):
    from . import utils
    app.before_request(utils.inject_search_data)


def init_login(app: Flask):
    from . import models

    @login_manager.user_loader
    def user_loader(user_id):
        return models.User.query.filter_by(id=int(user_id)).first()
