from flask import Flask
from flask_migrate import Migrate

from models import db
from webapp.main.views import blueprint as main_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(main_blueprint)
    return app
