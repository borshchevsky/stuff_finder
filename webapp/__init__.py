from flask import Flask
from models import db

from webapp.main.views import blueprint as main_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    db.init_app(app)

    app.register_blueprint(main_blueprint)
    return app
